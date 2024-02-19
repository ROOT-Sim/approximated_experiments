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

extern void RestoreApproximated(lp_id_t id, void *ptr, void *tmp);
void* PreRestoreApproximated(lp_id_t id, void *ptr);

#define RANGE_0_1   0
#define RANGE_1_1pC 1
#define RANGE_1_1pI 2
#define RANGE_0_1pI 3

#define BOUNDED 1
#define UNBOUNDED 0

#define C (left_value+1)


#if RANGE == RANGE_1_1pC || RANGE == RANGE_1_1pI
double left_value  = 1.0;
#endif
#if RANGE == RANGE_0_1 || RANGE == RANGE_0_1pI
double left_value  = 0.0;
#endif


#define TARGET_RELATIVE_ERROR 0.05
#define TARGET_ABSOLUTE_ERROR 0.05

#define P_ROLL 0.10
#define Z_BOUND 0.06
#define I_BOUND 2.00

struct simulation_configuration conf = {
    .lps = NUM_LPS,
    .n_threads = NUM_THREADS,
    .termination_time = 0,
    .gvt_period = 1000000,
    .log_level = LOG_SILENT,
    .stats_file = "root_sir_stats",
    .ckpt_interval = 0,
    .prng_seed = 0,
    .core_binding = false,
    .serial = false,
    .dispatcher = ProcessEvent,
    .committed = CanEnd,
    .restore = RestoreApproximated,
    .pre_restore = PreRestoreApproximated
};

static inline double extract_value(){
	switch(RANGE){
  	  case RANGE_0_1:
  		return Random();  	  	  	
  	  	break;
  	  case RANGE_1_1pC:
  		return left_value + Random();  	  	  	
  	  	break;
  	  case RANGE_0_1pI:
  	  	return Expent(1.0);	  	  	
  	  	break;
  	  case RANGE_1_1pI:
  	  	return left_value + Expent(1.0);	  	  	
  	  	break;
  	}
	return 0;
}

void RestoreApproximated(lp_id_t id, void *ptr, void *tmp) {
	double right_value = 0;
	
  #if RANGE == RANGE_0_1
	right_value = 1;
  #endif
  #if RANGE == RANGE_0_1pI || RANGE == RANGE_1_1pC
	right_value = 2;
  #endif
  #if RANGE == RANGE_1_1pI
	right_value = 3;
  #endif
	lp_state_type *state_ptr = (lp_state_type *) ptr;
	
	if(!ApproximatedMemoryCheck(state_ptr->abs_approx)){
		state_ptr->abs_approx  = rs_malloc(sizeof(buffer));
		ApproximatedMemoryMark(state_ptr->abs_approx, false);			
		state_ptr->abs_approx->value = left_value;
		state_ptr->abs_approx->value+= TARGET_ABSOLUTE_ERROR;
		state_ptr->abs_approx->value+= ((double)state_ptr->precise->abs_sentinel)*TARGET_ABSOLUTE_ERROR*2.0;
		//printf("precise %f approx %f sent %u\n", state_ptr->precise->value, 
		//state_ptr->abs_approx->value, state_ptr->precise->abs_sentinel);
	}

	
	if(!ApproximatedMemoryCheck(state_ptr->rel_approx)){  
		state_ptr->rel_approx  = rs_malloc(sizeof(buffer));
		ApproximatedMemoryMark(state_ptr->rel_approx, false);			
		state_ptr->rel_approx->value = right_value*(1-TARGET_RELATIVE_ERROR)/(1+TARGET_RELATIVE_ERROR);
		for(int i = 0;i<state_ptr->precise->rel_sentinel;i++)
			state_ptr->rel_approx->value *= (1-TARGET_RELATIVE_ERROR)/(1+TARGET_RELATIVE_ERROR);
		state_ptr->rel_approx->value *= (1+TARGET_RELATIVE_ERROR);
  }
}


static void update_state(lp_state_type *state_ptr, simtime_t now){
	state_ptr->precise_values[state_ptr->events] = state_ptr->precise->value;
	state_ptr->rel_approx_values[state_ptr->events]  = state_ptr->rel_approx->value;
	state_ptr->abs_approx_values[state_ptr->events]  = state_ptr->abs_approx->value;
	state_ptr->ts[state_ptr->events]  = now;

	state_ptr->events++;
	state_ptr->precise->value = extract_value();
	state_ptr->rel_approx->value = state_ptr->precise->value;
	state_ptr->abs_approx->value = state_ptr->precise->value;

	bool precise = false;
	double right_value = 0;
	ApproximatedMemoryMark(state_ptr->abs_approx, precise);
	ApproximatedMemoryMark(state_ptr->rel_approx, precise);

  #if RANGE == RANGE_1_1pI || RANGE == RANGE_0_1pI 
    // check right bound
	precise = precise || state_ptr->precise->value > left_value+I_BOUND; 
	ApproximatedMemoryMark(state_ptr->abs_approx, precise);
	ApproximatedMemoryMark(state_ptr->rel_approx, precise);
  #endif

  #if RANGE == RANGE_0_1 || RANGE == RANGE_0_1pI 
    // check left bound
	precise = precise || state_ptr->precise->value < Z_BOUND; 
	ApproximatedMemoryMark(state_ptr->abs_approx, precise);
	ApproximatedMemoryMark(state_ptr->rel_approx, precise);
  #endif
	
  #if RANGE == RANGE_0_1
	right_value = 1;
  #endif
  #if RANGE == RANGE_0_1pI || RANGE == RANGE_1_1pC
	right_value = 2;
  #endif
  #if RANGE == RANGE_1_1pI
	right_value = 3;
  #endif
	
	if(!precise){
		// abs error strategy
		state_ptr->precise->abs_sentinel = (unsigned char)((state_ptr->precise->value-left_value)/(TARGET_ABSOLUTE_ERROR*2.0));
		// rel error strategy
		state_ptr->precise->rel_sentinel = 0;
		
		double th_val = (1-TARGET_RELATIVE_ERROR)/(1+TARGET_RELATIVE_ERROR);
		double pr_val = state_ptr->precise->value;
		double cur_val = right_value*th_val;
		while(cur_val > pr_val){
			cur_val *= th_val;
			state_ptr->precise->rel_sentinel++;
		}
		double test = right_value*th_val;
		for(int i=0;i<state_ptr->precise->rel_sentinel;i++){
			test *= th_val;
		}
		test *= (1+TARGET_RELATIVE_ERROR);
		double err = test - pr_val;
		err = err < 0 ? -1.0 * err : err;
		err /= pr_val;
		if(err > TARGET_RELATIVE_ERROR){
			printf("failed to compute sentinel pr %f ap %f sen %u err %f\n", pr_val, test, state_ptr->precise->rel_sentinel, err);
			exit(1);
		}
	}


}

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

			state_ptr->precise 	   = rs_malloc(sizeof(buffer));
			state_ptr->rel_approx  = rs_malloc(sizeof(buffer));
			state_ptr->abs_approx  = rs_malloc(sizeof(buffer));

			update_state(state_ptr, now);

			ApproximatedModeSwitch(APPROXIMATED_MODE_APPROXIMATED);

			ScheduleNewEvent(me, 20 * Random(), LOOP, NULL, 0);
			break;


		case LOOP:
			ScheduleNewEvent(me, now + (Expent(tau)), LOOP, NULL, 0);
			if (Random() < 0.4)
				ScheduleNewEvent(NUM_LPS * Random(), now + (Expent(tau)), RECEIVE, NULL, 0);
		case RECEIVE:
			update_state(state_ptr, now);		
			break;

		case LP_FINI:
			for(int i =0; i< complete_events;i++){
				printf("%lu,%d,%f,%.10f,%.10f,%.10f\n", me, i, state_ptr->ts[i],
					state_ptr->precise_values[i],state_ptr->abs_approx_values[i],state_ptr->rel_approx_values[i]);
			}
			break;

		default:
			printf("[ERR] Requested to process an event neither ALLOC, nor DEALLOC, nor INIT\n");
			break;
	}
}

void* PreRestoreApproximated(lp_id_t id, void *ptr) {
	return NULL;
}

bool CanEnd(lp_id_t me, const lp_state_type *snapshot) {
	return snapshot->events >= complete_events;
}

int main(void) {
	RootsimInit(&conf);
	return RootsimRun();
}

