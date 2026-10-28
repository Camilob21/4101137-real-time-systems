/*
 * SoilSense Control, PROCPU image (week 8 on): everything around the hard path.
 * The console, telemetry, the flow batch and the display run here; sampling,
 * control and the e-stop run alone on APPCPU (../app_appcpu) and report over IPM.
 *
 * `load on` starts a thread that streams a 64 KB table out of flash through the
 * cache the two cores share: the synthetic load of the week-8 tail table.
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/ipm.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/sys/atomic.h>
#include <zephyr/sys/util.h>
#include <zephyr/sys/printk.h>
#ifdef CONFIG_THREAD_ANALYZER
#include <zephyr/debug/thread_analyzer.h>
#endif
#ifdef CONFIG_CHARACTER_FRAMEBUFFER
#include <zephyr/drivers/display.h>
#include <zephyr/display/cfb.h>
#endif
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "node_ipm.h"

#define TELEMETRY_MS 1000
#define FLOW_BATCH   100   /* pulses accumulated before the batch math runs */
#define CALIB_ROUNDS 1000
#define DISPLAY_MS   500

#define INSTR(node) GPIO_DT_SPEC_GET_OR(DT_NODELABEL(node), gpios, {0})
static const struct gpio_dt_spec instr_cons = INSTR(instr_cons);
static const struct gpio_dt_spec instr_tele = INSTR(instr_tele);
static const struct gpio_dt_spec instr_flow = INSTR(instr_flow);
static const struct gpio_dt_spec instr_disp = INSTR(instr_disp);
static const struct gpio_dt_spec instr_ipm = INSTR(instr_ipm);
static const struct gpio_dt_spec flow_pulse =
	GPIO_DT_SPEC_GET_OR(DT_NODELABEL(flow_pulse), gpios, {0});

static const struct device *const ipm = DEVICE_DT_GET(DT_NODELABEL(ipm0));
static const struct device *const console_uart = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));
#ifdef CONFIG_CHARACTER_FRAMEBUFFER
static const struct device *const disp = DEVICE_DT_GET_ANY(solomon_ssd1306);
#endif

static inline void instr_set(const struct gpio_dt_spec *p, int v)
{
	if (p->port) {
		gpio_pin_set_dt(p, v);
	}
}

/* ---- The hard path's state, as APPCPU last reported it -------------------- */

static struct node_status node;
static struct k_spinlock node_lock;
static uint32_t status_msgs;

/* Runs in interrupt context: copy the slot before APPCPU can overwrite it. */
static void ipm_rx(const struct device *dev, void *user_data, uint32_t id,
		   volatile void *data)
{
	if (id != MSG_STATUS) {
		return;
	}

	struct node_status s;

	memcpy(&s, (const void *)data, sizeof(s));
	if (s.estop && !node.estop) {
		instr_set(&instr_ipm, 1); /* the e-stop has crossed the cores */
	} else if (!s.estop) {
		instr_set(&instr_ipm, 0);
	}

	K_SPINLOCK(&node_lock) {
		node = s;
		status_msgs++;
	}
}

static struct node_status node_get(void)
{
	struct node_status s;

	K_SPINLOCK(&node_lock) {
		s = node;
	}
	return s;
}

static void node_send(enum node_msg id, int32_t value)
{
	(void)ipm_send(ipm, 1, id, &value, sizeof(value));
}

/* ---- Flow: counted in the ISR, each full batch deferred to flow_wq --------- */

static atomic_t flow_pulses;
static struct gpio_callback flow_cb;
static struct k_work_q flow_wq;
static struct k_work flow_work;
static float flow_lpm;        /* float on purpose: no FPU */
static uint32_t flow_batches;

static void flow_isr(const struct device *dev, struct gpio_callback *cb, uint32_t pins)
{
	if (atomic_inc(&flow_pulses) + 1 >= FLOW_BATCH) {
		k_work_submit_to_queue(&flow_wq, &flow_work);
	}
}

static void flow_work_fn(struct k_work *work)
{
	if (atomic_get(&flow_pulses) < FLOW_BATCH) {
		return;
	}
	instr_set(&instr_flow, 1);

	float pulses = (float)atomic_clear(&flow_pulses);
	float lpm = pulses / 5880.0f * 60.0f; /* YF-S401: 5880 pulses/L */

	for (int i = 0; i < 50; i++) {
		flow_lpm = flow_lpm * 0.9f + lpm * 0.1f;
	}
	flow_batches++;

	instr_set(&instr_flow, 0);
}

/* ---- Synthetic load: one read per cache line of a table that lives in flash - */

static const uint8_t load_table[64 * 1024] = { 1 };
static atomic_t load_on;

static void load_thread(void *p1, void *p2, void *p3)
{
	volatile uint32_t sum = 0;

	while (1) {
		if (!atomic_get(&load_on)) {
			k_msleep(100);
			continue;
		}
		for (size_t i = 0; i < sizeof(load_table); i += 32) {
			sum += load_table[i];
		}
	}
}

/* ---- Telemetry, display, console ------------------------------------------ */

static void task_telemetry(void)
{
	struct node_status s = node_get();

	instr_set(&instr_tele, 1);
	printk("t=%u p_mv=%d sp_mv=%d duty=%d flow_x100=%d estop=%d backlog=%u\n",
	       (unsigned int)k_uptime_get(), s.pressure_mv, s.setpoint_mv, s.duty_pct,
	       (int)(flow_lpm * 100.0f), s.estop, s.backlog_peak);
	instr_set(&instr_tele, 0);
}

#ifdef CONFIG_CHARACTER_FRAMEBUFFER
static void task_display(void)
{
	static bool ready;
	char line[24];
	struct node_status s = node_get();

	if (disp == NULL) {
		return;
	}
	if (!ready) {
		if (!device_is_ready(disp) || cfb_framebuffer_init(disp) != 0) {
			return;
		}
		display_blanking_off(disp);
		ready = true;
	}

	instr_set(&instr_disp, 1);
	cfb_framebuffer_clear(disp, false);
	snprintf(line, sizeof(line), "P %4d>%4dmV", s.pressure_mv, s.setpoint_mv);
	cfb_print(disp, line, 0, 0);
	snprintf(line, sizeof(line), "duty %3d%% %s", s.duty_pct, s.estop ? "ESTOP" : "");
	cfb_print(disp, line, 0, 16);
	snprintf(line, sizeof(line), "flow %d.%02d L/m", (int)flow_lpm,
		 (int)(flow_lpm * 100.0f) % 100);
	cfb_print(disp, line, 0, 32);
	cfb_framebuffer_finalize(disp);
	instr_set(&instr_disp, 0);
}
#else
static void task_display(void)
{
}
#endif

static void cmd_calib(void)
{
	printk("calibrating zero-flow offset (%d rounds)...\n", CALIB_ROUNDS);
	for (int i = 0; i < CALIB_ROUNDS; i++) {
		k_usleep(400); /* sensor settling time between reads */
	}
	printk("calibration done\n");
}

static void console_handle(char *line)
{
	if (strcmp(line, "help") == 0) {
		printk("commands: help status set <mv> clear calib load on|off threads\n");
	} else if (strcmp(line, "status") == 0) {
		struct node_status s = node_get();

		printk("p=%d mV sp=%d mV duty=%d%% flow_x100=%d estop=%d batches=%u "
		       "backlog_peak=%u lat_peak_us=%u ipm_msgs=%u load=%s\n",
		       s.pressure_mv, s.setpoint_mv, s.duty_pct, (int)(flow_lpm * 100.0f),
		       s.estop, flow_batches, s.backlog_peak, s.lat_peak_us, status_msgs,
		       atomic_get(&load_on) ? "on" : "off");
	} else if (strncmp(line, "set ", 4) == 0) {
		int32_t mv = CLAMP(atoi(line + 4), 0, 3300);

		node_send(MSG_SETPOINT, mv);
		printk("setpoint = %d mV\n", mv);
	} else if (strcmp(line, "clear") == 0) {
		node_send(MSG_CLEAR, 0);
		printk("e-stop cleared\n");
	} else if (strcmp(line, "calib") == 0) {
		cmd_calib();
	} else if (strcmp(line, "load on") == 0 || strcmp(line, "load off") == 0) {
		atomic_set(&load_on, line[6] == 'n');
		printk("load %s\n", atomic_get(&load_on) ? "on" : "off");
#ifdef CONFIG_THREAD_ANALYZER
	} else if (strcmp(line, "threads") == 0) {
		thread_analyzer_print(0);
#endif
	} else if (line[0] != '\0') {
		printk("? (try: help)\n");
	}
}

static void task_console(void)
{
	static char buf[32];
	static size_t len;
	unsigned char c;

	while (uart_poll_in(console_uart, &c) == 0) {
		instr_set(&instr_cons, 1);
		if (c == '\r' || c == '\n') {
			buf[len] = '\0';
			printk("\n");
			console_handle(buf);
			len = 0;
		} else if (len < sizeof(buf) - 1) {
			buf[len++] = c;
			printk("%c", c);
		}
		instr_set(&instr_cons, 0);
	}
}

/* ---- Threads: the week-4 priorities, minus the two that moved to APPCPU ----- */

#define FLOW_WQ_PRIO   5
#define DISPLAY_PRIO   7
#define TELEMETRY_PRIO 8
#define CONSOLE_PRIO   9
#define LOAD_PRIO      10

static void display_thread(void *p1, void *p2, void *p3)
{
	while (1) {
		task_display();
		k_msleep(DISPLAY_MS);
	}
}
K_THREAD_DEFINE(display_tid, 2048, display_thread, NULL, NULL, NULL, DISPLAY_PRIO, 0, 0);

static void telemetry_thread(void *p1, void *p2, void *p3)
{
	int64_t next_ms = k_uptime_get();

	while (1) {
		task_telemetry();
		next_ms += TELEMETRY_MS;
		k_sleep(K_TIMEOUT_ABS_MS(next_ms));
	}
}
K_THREAD_DEFINE(telemetry_tid, 2048, telemetry_thread, NULL, NULL, NULL, TELEMETRY_PRIO, 0, 0);

static void console_thread(void *p1, void *p2, void *p3)
{
	while (1) {
		task_console();
		k_msleep(5);
	}
}
K_THREAD_DEFINE(console_tid, 2048, console_thread, NULL, NULL, NULL, CONSOLE_PRIO, 0, 0);

K_THREAD_DEFINE(load_tid, 1024, load_thread, NULL, NULL, NULL, LOAD_PRIO, 0, 0);

K_THREAD_STACK_DEFINE(flow_wq_stack, 1024);

int main(void)
{
	const struct k_work_queue_config flow_wq_cfg = { .name = "flow_wq" };
	const struct gpio_dt_spec *outs[] = { &instr_cons, &instr_tele, &instr_flow,
					      &instr_disp, &instr_ipm };

	k_work_queue_start(&flow_wq, flow_wq_stack, K_THREAD_STACK_SIZEOF(flow_wq_stack),
			   FLOW_WQ_PRIO, &flow_wq_cfg);
	k_work_init(&flow_work, flow_work_fn);

	for (size_t i = 0; i < ARRAY_SIZE(outs); i++) {
		if (outs[i]->port) {
			gpio_pin_configure_dt(outs[i], GPIO_OUTPUT_INACTIVE);
		}
	}
	if (flow_pulse.port) {
		gpio_pin_configure_dt(&flow_pulse, GPIO_INPUT);
		gpio_pin_interrupt_configure_dt(&flow_pulse, GPIO_INT_EDGE_TO_ACTIVE);
		gpio_init_callback(&flow_cb, flow_isr, BIT(flow_pulse.pin));
		gpio_add_callback(flow_pulse.port, &flow_cb);
	}

	ipm_register_callback(ipm, ipm_rx, NULL);
	printk("SoilSense Control — AMP node, PROCPU (%s)\n", CONFIG_BOARD);
	printk("type 'help'\n");
	return 0;
}
