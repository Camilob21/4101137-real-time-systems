/*
 * Lab 6, Task A — Buttazzo Fig. 4.13 on the ESP32-S3.
 *
 *   tau1: C = 2 ms, T = D = 5 ms     tau2: C = 4 ms, T = D = 7 ms
 *   U = 2/5 + 4/7 = 0.971  (> 0.828, Liu & Layland for n = 2; <= 1, EDF)
 *
 * RM  (default build):            tau1 prio 4, tau2 prio 5 -> tau2 misses at t = 7 ms.
 * EDF (-DEXTRA_CONF_FILE=edf.conf): both prio 5, ordered by absolute deadline.
 *
 * "Computation" is a calibrated busy loop: it burns CPU *time*, so a preempted
 * job still owes its remaining C when it resumes. (k_busy_wait would not do:
 * it counts wall-clock time, and a job preempted inside it would end early.)
 *
 * Analyzer pins (same header pins as the node, so the clips stay put):
 *   GPIO4  tau1 running its job (high = job started and not finished)
 *   GPIO5  tau2 running its job
 *   GPIO6  10 us pulse each time a job finishes after its deadline (a miss)
 *   GPIO7  10 us pulse at the start of every hyperperiod (35 ms, t = 0 of the figure)
 */

#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/sys/printk.h>

#define T1_US 5000
#define C1_US 2000
#define T2_US 7000
#define C2_US 4000
#define HYPER_JOBS_T1 7 /* 35 ms / 5 ms */

#ifdef CONFIG_SCHED_DEADLINE
#define MODE_NAME "EDF"
#define PRIO_T1 5
#define PRIO_T2 5 /* same static priority: the deadline decides */
#else
#define MODE_NAME "RM"
#define PRIO_T1 4 /* shorter period -> higher priority */
#define PRIO_T2 5
#endif
#define PRIO_REPORT 10 /* below both: it only gets the idle time */

#define PIN(node) GPIO_DT_SPEC_GET_OR(DT_NODELABEL(node), gpios, {0})
static const struct gpio_dt_spec pin_t1 = PIN(instr_samp);   /* GPIO4 */
static const struct gpio_dt_spec pin_t2 = PIN(instr_ctrl);   /* GPIO5 */
static const struct gpio_dt_spec pin_miss = PIN(instr_cons); /* GPIO6 */
static const struct gpio_dt_spec pin_hyper = PIN(instr_tele); /* GPIO7 */

static inline void pin_set(const struct gpio_dt_spec *p, int v)
{
	if (p->port) {
		gpio_pin_set_dt(p, v);
	}
}

static void pin_pulse(const struct gpio_dt_spec *p)
{
	pin_set(p, 1);
	k_busy_wait(10);
	pin_set(p, 0);
}

/* ---- Calibrated CPU burn ------------------------------------------------- */

static uint32_t loops_per_ms;

static void __noinline spin(uint32_t n)
{
	for (volatile uint32_t i = 0; i < n; i++) {
	}
}

static void burn_us(uint32_t us)
{
#ifdef CONFIG_ARCH_POSIX
	for (uint32_t i = 0; i < us / 10U; i++) {
		k_busy_wait(10); /* native_sim: no cycle-accurate CPU, burn in slices */
	}
#else
	spin((uint32_t)(((uint64_t)loops_per_ms * us) / 1000U));
#endif
}

static uint32_t measure_us(uint32_t loops)
{
	uint32_t c0 = k_cycle_get_32();

	spin(loops);
	return k_cyc_to_us_near32(k_cycle_get_32() - c0);
}

static void calibrate(void)
{
	const uint32_t probe = 200000;
	uint32_t us;

	(void)measure_us(probe); /* first run warms the cache */
	us = measure_us(probe);
	loops_per_ms = (uint32_t)(((uint64_t)probe * 1000U) / MAX(us, 1U));

	uint32_t c0 = k_cycle_get_32();

	burn_us(C1_US);
	uint32_t got1 = k_cyc_to_us_near32(k_cycle_get_32() - c0);

	c0 = k_cycle_get_32();
	burn_us(C2_US);
	uint32_t got2 = k_cyc_to_us_near32(k_cycle_get_32() - c0);

	printk("calibration: %u loops/ms; burn(2000 us) = %u us, burn(4000 us) = %u us\n",
	       loops_per_ms, got1, got2);
}

/* ---- One time base for releases, deadlines and measurements -------------- */

/* Releases are absolute kernel ticks (100 us on the S3, so 5 and 7 ms are
 * exact). Deadlines for k_thread_absolute_deadline_set() and the response
 * times are in the k_cycle_get_32() domain. cyc_at_tick0 ties the two:
 * cycles = cyc_at_tick0 + ticks * cycles_per_tick, all modulo 2^32. */
static uint32_t cyc_at_tick0;

static void timebase_sync(void)
{
	int64_t t = k_uptime_ticks();
	int64_t t1;

	do {
#ifdef CONFIG_ARCH_POSIX
		k_busy_wait(1); /* native_sim: time only moves when the CPU waits */
#endif
		t1 = k_uptime_ticks();
	} while (t1 == t); /* wait for a tick boundary... */
	uint32_t c = k_cycle_get_32(); /* ...and read the cycle counter right on it */

	cyc_at_tick0 = c - (uint32_t)k_ticks_to_cyc_floor64(t1);
}

static inline uint32_t tick_to_cyc(int64_t ticks)
{
	return cyc_at_tick0 + (uint32_t)k_ticks_to_cyc_floor64(ticks);
}

/* ---- The two periodic tasks --------------------------------------------- */

struct ptask {
	const char *name;
	int id;
	uint32_t C_us;
	uint32_t T_us;
	const struct gpio_dt_spec *pin;
	/* statistics, written by the task, read by the reporter */
	volatile uint32_t jobs;
	volatile uint32_t misses;
	volatile uint32_t r_max_us;
	volatile uint32_t late_max_us; /* worst finish past the deadline */
};

static struct ptask tau1 = { "tau1", 1, C1_US, T1_US, &pin_t1 };
static struct ptask tau2 = { "tau2", 2, C2_US, T2_US, &pin_t2 };

static int64_t t0_ticks; /* common first release of both tasks */

/* First miss, frozen for the report */
static volatile bool first_miss_seen;
static volatile int fm_task;
static volatile uint32_t fm_job, fm_dl_us, fm_fin_us;

static void task_fn(void *p1, void *p2, void *p3)
{
	struct ptask *t = p1;
	const int64_t T_ticks = k_us_to_ticks_floor64(t->T_us);
	int64_t rel = t0_ticks;

	for (uint32_t k = 0;; k++) {
		const int64_t dl = rel + T_ticks; /* D = T */

#ifdef CONFIG_SCHED_DEADLINE
		/* Before blocking: the job that will wake up already carries its
		 * own absolute deadline when the kernel picks who runs. */
		k_thread_absolute_deadline_set(k_current_get(), (int)tick_to_cyc(dl));
#endif
		if (rel > k_uptime_ticks()) {
			k_sleep(K_TIMEOUT_ABS_TICKS(rel)); /* wait for the release */
		} /* else: the previous job ran late, this one is already released */

		if (t->id == 1 && (k % HYPER_JOBS_T1) == 0) {
			pin_pulse(&pin_hyper);
		}

		pin_set(t->pin, 1);
		burn_us(t->C_us);
		pin_set(t->pin, 0);

		const uint32_t fin = k_cycle_get_32();
		const uint32_t r_us = k_cyc_to_us_floor32(fin - tick_to_cyc(rel));
		const int32_t late = (int32_t)(fin - tick_to_cyc(dl));

		t->jobs++;
		if (r_us > t->r_max_us) {
			t->r_max_us = r_us;
		}
		if (late > 0) {
			const uint32_t late_us = k_cyc_to_us_floor32((uint32_t)late);

			if (late_us > t->late_max_us) {
				t->late_max_us = late_us;
			}
			t->misses++;
			pin_pulse(&pin_miss);
			if (!first_miss_seen) {
				fm_task = t->id;
				fm_job = k;
				fm_dl_us = k_cyc_to_us_floor32(tick_to_cyc(dl) - tick_to_cyc(t0_ticks));
				fm_fin_us = k_cyc_to_us_floor32(fin - tick_to_cyc(t0_ticks));
				first_miss_seen = true;
			}
		}
		rel += T_ticks;
	}
}

K_THREAD_STACK_DEFINE(stack1, 1024);
K_THREAD_STACK_DEFINE(stack2, 1024);
static struct k_thread th1, th2;

/* ---- Reporter: one line per second, from idle time only ----------------- */

static void reporter_fn(void *p1, void *p2, void *p3)
{
	int64_t next = t0_ticks;
	uint32_t s = 0;
	bool fm_printed = false;

	while (1) {
		next += k_ms_to_ticks_floor64(1000);
		k_sleep(K_TIMEOUT_ABS_TICKS(next));
		s++;
		printk("[%s] t=%3us | tau1 jobs=%6u miss=%5u Rmax=%5u us | "
		       "tau2 jobs=%6u miss=%5u Rmax=%5u us late_max=%4u us\n",
		       MODE_NAME, s, tau1.jobs, tau1.misses, tau1.r_max_us,
		       tau2.jobs, tau2.misses, tau2.r_max_us, tau2.late_max_us);
		if (first_miss_seen && !fm_printed) {
			printk("[%s] first miss: tau%d, job %u, deadline t=%u.%03u ms, "
			       "finished t=%u.%03u ms (t=0: first common release)\n",
			       MODE_NAME, fm_task, fm_job, fm_dl_us / 1000, fm_dl_us % 1000,
			       fm_fin_us / 1000, fm_fin_us % 1000);
			fm_printed = true;
		}
	}
}

K_THREAD_STACK_DEFINE(stack_r, 2048);
static struct k_thread th_r;

int main(void)
{
	const struct gpio_dt_spec *pins[] = { &pin_t1, &pin_t2, &pin_miss, &pin_hyper };

	for (size_t i = 0; i < ARRAY_SIZE(pins); i++) {
		if (pins[i]->port) {
			gpio_pin_configure_dt(pins[i], GPIO_OUTPUT_INACTIVE);
		}
	}

	printk("\nLab 6 Task A - Fig. 4.13 under %s (%s)\n", MODE_NAME, CONFIG_BOARD);
	printk("tau1 C=%u T=%u us prio %d | tau2 C=%u T=%u us prio %d | tick = %u us\n",
	       C1_US, T1_US, PRIO_T1, C2_US, T2_US, PRIO_T2,
	       1000000U / CONFIG_SYS_CLOCK_TICKS_PER_SEC);
	calibrate();
	timebase_sync();

	t0_ticks = k_uptime_ticks() + k_ms_to_ticks_floor64(1000); /* start in 1 s */

	k_thread_create(&th1, stack1, K_THREAD_STACK_SIZEOF(stack1), task_fn,
			&tau1, NULL, NULL, PRIO_T1, 0, K_NO_WAIT);
	k_thread_name_set(&th1, "tau1");
	k_thread_create(&th2, stack2, K_THREAD_STACK_SIZEOF(stack2), task_fn,
			&tau2, NULL, NULL, PRIO_T2, 0, K_NO_WAIT);
	k_thread_name_set(&th2, "tau2");
	k_thread_create(&th_r, stack_r, K_THREAD_STACK_SIZEOF(stack_r), reporter_fn,
			NULL, NULL, NULL, PRIO_REPORT, 0, K_NO_WAIT);
	k_thread_name_set(&th_r, "report");
	return 0;
}
