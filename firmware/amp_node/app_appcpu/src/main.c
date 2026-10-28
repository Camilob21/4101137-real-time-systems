/*
 * SoilSense Control, APPCPU image (week 8 on): the hard path alone on the second
 * core. Sampling at 1 kHz, control every 10th sample, the e-stop check and the
 * valve, on the synthetic plant. No console: PROCPU (../app_procpu) owns everything
 * with a person or a driver on the other end, and the two talk over IPM.
 *
 * The code runs from flash through a cache both cores share, so a busy PROCPU still
 * stalls it; iram.conf moves the hard path to internal RAM.
 */

#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/ipm.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/util.h>

#include "node_ipm.h"

#ifdef CONFIG_APP_HARD_PATH_IRAM
/* In internal RAM, off the flash cache that both cores share (iram.conf). */
#include <hal/gpio_ll.h>
#define HARD __attribute__((section(".iram1.hard")))
#else
#define HARD
#endif

#define SAMPLE_PERIOD_US 1000
#define CONTROL_EVERY    10    /* control every 10th sample -> 10 ms */
#define STATUS_EVERY     10    /* status to PROCPU every 10th control -> 10 Hz */
#define PWM_STEPS        20    /* software PWM on the valve: 1 kHz / 20 = 50 Hz */
#define ESTOP_MV         3000

#define INSTR(node) GPIO_DT_SPEC_GET_OR(DT_NODELABEL(node), gpios, {0})
enum { HP_SAMP, HP_CTRL, HP_VALVE };
static const struct gpio_dt_spec pins[] = {
	[HP_SAMP] = INSTR(instr_samp),
	[HP_CTRL] = INSTR(instr_ctrl),
	[HP_VALVE] = GPIO_DT_SPEC_GET_OR(DT_ALIAS(led0), gpios, {0}),
};
static const struct device *const ipm = DEVICE_DT_GET(DT_NODELABEL(ipm0));

#ifdef CONFIG_APP_HARD_PATH_IRAM
/* The specs and the GPIO driver live in flash: copy the pin numbers to RAM. */
static uint32_t pin_num[ARRAY_SIZE(pins)];
static bool pin_ok[ARRAY_SIZE(pins)];
#endif

static inline void pin_set(int i, int v)
{
#ifdef CONFIG_APP_HARD_PATH_IRAM
	if (pin_ok[i]) {
		gpio_ll_set_level(&GPIO, pin_num[i], v);
	}
#else
	if (pins[i].port) {
		gpio_pin_set_dt(&pins[i], v);
	}
#endif
}

K_MSGQ_DEFINE(tick_q, sizeof(uint32_t), 8, 4);
K_SEM_DEFINE(control_sem, 0, CONTROL_EVERY);
static atomic_t backlog_peak;
static atomic_t lat_peak_us;

HARD static void tick_isr(struct k_timer *t)
{
	uint32_t released = k_cycle_get_32();

	k_msgq_put(&tick_q, &released, K_NO_WAIT);

	atomic_val_t backlog = k_msgq_num_used_get(&tick_q);

	if (backlog > atomic_get(&backlog_peak)) {
		atomic_set(&backlog_peak, backlog);
	}
}
K_TIMER_DEFINE(tick_timer, tick_isr, NULL);

/* Written by PROCPU's commands (IPM callback), read by the hard path. */
static atomic_t setpoint_mv = ATOMIC_INIT(1500);
static atomic_t clear_req;

static int pressure_mv;
static int duty_pct;
static int integral_mv;
static bool estop;

/* Pressure drifts toward what the valve commands. */
HARD static int plant_mv(void)
{
	static int mv = 1200;

	mv += (duty_pct * 33 - mv) / 64;
	mv += (int)(k_cycle_get_32() % 7) - 3;
	return mv;
}

HARD static void send_status(void)
{
	struct node_status s = {
		.pressure_mv = pressure_mv,
		.setpoint_mv = atomic_get(&setpoint_mv),
		.duty_pct = duty_pct,
		.estop = estop,
		.lat_peak_us = atomic_get(&lat_peak_us),
		.backlog_peak = atomic_get(&backlog_peak),
	};

	(void)ipm_send(ipm, 1, MSG_STATUS, &s, sizeof(s));
}

HARD static void task_sampling(void)
{
	static int pwm_phase;

	pin_set(HP_SAMP, 1);

	pressure_mv = plant_mv();

	/* ADR-005: detect and close the valve in the same job, then tell PROCPU. */
	bool tripped = false;

	if (pressure_mv > ESTOP_MV) {
		tripped = !estop;
		estop = true;
		duty_pct = 0;
	}

	pwm_phase = (pwm_phase + 1) % PWM_STEPS;
	pin_set(HP_VALVE, pwm_phase < (duty_pct * PWM_STEPS) / 100);

	if (tripped) {
		send_status();
	}

	pin_set(HP_SAMP, 0);
}

HARD static void task_control(void)
{
	static int status_div;

	pin_set(HP_CTRL, 1);

	if (atomic_clear(&clear_req)) {
		estop = false;
		integral_mv = 0;
	}
	if (estop) {
		duty_pct = 0;
	} else {
		int error = atomic_get(&setpoint_mv) - pressure_mv;

		integral_mv += error / 8;
		integral_mv = CLAMP(integral_mv, -2000, 2000);
		duty_pct = CLAMP((error + integral_mv) / 20, 0, 100);
	}

	pin_set(HP_CTRL, 0);

	if (++status_div >= STATUS_EVERY) {
		status_div = 0;
		send_status();
	}
}

/* Runs in interrupt context: store and leave. */
HARD static void ipm_rx(const struct device *dev, void *user_data, uint32_t id,
		   volatile void *data)
{
	if (id == MSG_SETPOINT) {
		atomic_set(&setpoint_mv, *(volatile int32_t *)data);
	} else if (id == MSG_CLEAR) {
		atomic_set(&clear_req, 1);
	}
}

HARD static void sampling_thread(void *p1, void *p2, void *p3)
{
	uint32_t released;
	int control_div = 0;

	while (1) {
		k_msgq_get(&tick_q, &released, K_FOREVER);

		atomic_val_t lat = k_cyc_to_us_floor32(k_cycle_get_32() - released);

		if (lat > atomic_get(&lat_peak_us)) {
			atomic_set(&lat_peak_us, lat);
		}

		task_sampling();
		if (++control_div >= CONTROL_EVERY) {
			control_div = 0;
			k_sem_give(&control_sem);
		}
	}
}
K_THREAD_DEFINE(sampling_tid, 1536, sampling_thread, NULL, NULL, NULL, 2, 0, 0);

HARD static void control_thread(void *p1, void *p2, void *p3)
{
	while (1) {
		k_sem_take(&control_sem, K_FOREVER);
		task_control();
	}
}
K_THREAD_DEFINE(control_tid, 1024, control_thread, NULL, NULL, NULL, 3, 0, 0);

int main(void)
{
	for (size_t i = 0; i < ARRAY_SIZE(pins); i++) {
		if (pins[i].port) {
			gpio_pin_configure_dt(&pins[i], GPIO_OUTPUT_INACTIVE);
#ifdef CONFIG_APP_HARD_PATH_IRAM
			pin_num[i] = pins[i].pin;
			pin_ok[i] = true;
#endif
		}
	}
	ipm_register_callback(ipm, ipm_rx, NULL);
	k_timer_start(&tick_timer, K_USEC(SAMPLE_PERIOD_US), K_USEC(SAMPLE_PERIOD_US));
	return 0;
}
