/*
 * Messages between the node's two images. IPM gives one slot each way: a message
 * not yet read is overwritten by the next, so every status carries the full state.
 */

#ifndef NODE_IPM_H_
#define NODE_IPM_H_

#include <stdint.h>

enum node_msg {
	MSG_STATUS = 1,   /* APPCPU -> PROCPU: 10 Hz, and at once when the e-stop trips */
	MSG_SETPOINT = 2, /* PROCPU -> APPCPU: int32_t, mV */
	MSG_CLEAR = 3,    /* PROCPU -> APPCPU: no payload */
};

struct node_status {
	int32_t pressure_mv;
	int32_t setpoint_mv;
	int32_t duty_pct;
	int32_t estop;
	uint32_t lat_peak_us;
	uint32_t backlog_peak;
};

#endif
