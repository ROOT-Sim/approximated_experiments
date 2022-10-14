#include "application.h"

#include "config.h"

#include <memory.h>


static unsigned max_buffers = MAX_BUFFERS;
static unsigned max_buffer_size = MAX_BUFFER_SIZE;
static unsigned complete_events = COMPLETE_EVENTS;
static double tau = TAU,
		send_probability = SEND_PROBABILITY,
		alloc_probability = ALLOC_PROBABILITY,
		dealloc_probability = DEALLOC_PROBABILITY;

extern void
ProcessEvent(lp_id_t me, simtime_t now, unsigned event_type, const unsigned *event_content, unsigned int event_size,
			 void *state);

extern bool CanEnd(lp_id_t me, const lp_state_type *snapshot);

extern void RestoreApproximated(lp_id_t id, void *ptr);

struct simulation_configuration conf = {
    .lps = NUM_LPS,
    .n_threads = NUM_THREADS,
    .termination_time = 0,
    .gvt_period = 100000,
    .log_level = LOG_SILENT,
    .stats_file = "root_sir_stats",
    .ckpt_interval = 0,
    .prng_seed = 0,
    .core_binding = false,
    .serial = false,
    .dispatcher = ProcessEvent,
    .committed = CanEnd,
    .restore = RestoreApproximated
};

void
ProcessEvent(lp_id_t me, simtime_t now, unsigned event_type, const unsigned *event_content, unsigned int event_size,
			 void *state) {
	lp_state_type *state_ptr = (lp_state_type *) state;

	if (now != 0.0 && state_ptr->events >= complete_events)
		return;

	switch (event_type) {

		case LP_INIT:
			state_ptr = rs_malloc(sizeof(lp_state_type));
			if (state_ptr == NULL) {
				exit(-1);
			}
			memset(state_ptr, 0, sizeof(lp_state_type));

			SetState(state_ptr);

			unsigned buffers_to_allocate = (unsigned) (Random() * max_buffers);

			unsigned robba_allocata = 0;
			for (unsigned i = 0; i < buffers_to_allocate; i++) {
				state_ptr->head = allocate_buffer(state_ptr->head, NULL,
												  (unsigned) (Random() * max_buffer_size) / sizeof(unsigned));
				state_ptr->buffer_count++;
				robba_allocata += state_ptr->head->count;
			}

			while (robba_allocata < buffers_to_allocate * max_buffer_size) {
				state_ptr->head = allocate_buffer(state_ptr->head, NULL,
												  (unsigned) (Random() * max_buffer_size) / sizeof(unsigned));
				state_ptr->buffer_count++;
				robba_allocata += state_ptr->head->count;
			}

			ApproximatedModeSwitch(EXEC_MODE);

			ScheduleNewEvent(me, 20 * Random(), LOOP, NULL, 0);
			break;


		case LOOP:
			state_ptr->events++;
			simtime_t timestamp = now + (Expent(tau));
			ScheduleNewEvent(me, timestamp, LOOP, NULL, 0);
			if (Random() < 0.2)
				ScheduleNewEvent(NUM_LPS * Random(), timestamp, LOOP, NULL, 0);

			if (state_ptr->buffer_count)
				state_ptr->total_checksum ^= read_buffer(state_ptr->head,
														 (unsigned) (Random() * state_ptr->buffer_count));

			if (state_ptr->buffer_count < max_buffers && Random() < alloc_probability) {
				state_ptr->head = allocate_buffer(state_ptr->head, NULL,
												  (unsigned) (Random() * max_buffer_size) / sizeof(unsigned));
				state_ptr->buffer_count++;
			}

			if (state_ptr->buffer_count && Random() < dealloc_probability) {
				state_ptr->head = deallocate_buffer(state_ptr->head, (unsigned) (Random() * state_ptr->buffer_count));
				state_ptr->buffer_count--;
			}

			if (state_ptr->buffer_count && Random() < send_probability) {
				unsigned i = (unsigned) (Random() * state_ptr->buffer_count);
				buffer *to_send = get_buffer(state_ptr->head, i);
				timestamp = now + (Expent(tau));

				ScheduleNewEvent(NUM_LPS * Random(), timestamp, RECEIVE, to_send->data,
								 to_send->count * sizeof(unsigned));

				state_ptr->head = deallocate_buffer(state_ptr->head, i);
				state_ptr->buffer_count--;
			}
			break;

		case RECEIVE:
			if (state_ptr->buffer_count >= max_buffers)
				break;
			state_ptr->head = allocate_buffer(state_ptr->head, event_content, event_size / sizeof(unsigned));
			state_ptr->buffer_count++;
			break;

		case LP_FINI:
#ifndef NDEBUG
			//printf("[LP %lu] total_checksum = %u\n", me, state_ptr->total_checksum);
#endif
			break;

		default:
			printf("[ERR] Requested to process an event neither ALLOC, nor DEALLOC, nor INIT\n");
			break;
	}
}

void RestoreApproximated(lp_id_t id, void *ptr) {
	lp_state_type *state = (lp_state_type *) ptr;
	unsigned i = state->buffer_count;
	buffer *tmp = state->head;

	while (i--) {
		if (rs_is_alloced(tmp->data))
			continue;
		tmp->data = rs_malloc(sizeof(*tmp->data) * tmp->count);
		ApproximatedMemoryMark(tmp->data, false);
		for (unsigned j = 0; j < tmp->count; j++) {
			tmp->data[j] = RandomRange(0, INT_MAX);
		}
		tmp = tmp->next;
	}
}

bool CanEnd(lp_id_t me, const lp_state_type *snapshot) {
	return snapshot->events >= complete_events;
}

int main(void) {
	RootsimInit(&conf);
	return RootsimRun();
}

