#include "application.h"
#include "config.h"
#include "parameters.h"
#include "guy.h"
#include "guy_init.h"

#include <math.h>
#include <stdio.h>
#include <time.h>

double infection_p = P_INFECT;

// From Luc Devroye's book "Non-Uniform Random Variate Generation." p. 522
unsigned random_binomial(unsigned trials, double p, struct drand48_data *rng_state)
{ // this is exposed since it is used also in guy.c
	if(p >= 1.0 || !trials) {
		return trials;
	}
	unsigned x = 0;
	double sum = 0, log_q = log(1.0 - p); // todo cache those logarithm value
	while(1) {
		double r;
		drand48_r(rng_state, &r);
		sum += log(r) / (trials - x);
		if(sum < log_q || trials == x) {
			return x;
		}
		x++;
	}
}

union event_t {
	const struct guy_t *agents;
	const infection_t *i_m;
	const init_t *in_m;
	const unsigned *phase;
};

extern void ProcessEvent(lp_id_t me, simtime_t now, unsigned event_type, union event_t event_content, unsigned int event_size, region_t *state);
extern bool CanEnd(lp_id_t me, const void *snapshot);
extern void RestoreApproximated(lp_id_t id, void *ptr);

struct simulation_configuration conf = {
    .lps = NUM_LPS,
    .n_threads = NUM_THREADS,
    .termination_time = 1000,
    .gvt_period = 1000000,
    .log_level = LOG_SILENT,
    .stats_file = "root_sir_stats",
    .ckpt_interval = 0,
    .prng_seed = 0,
    .core_binding = true,
    .serial = false,
    .dispatcher = ProcessEvent,
    .committed = CanEnd,
    .restore = RestoreApproximated
};

// we handle infects visits move at slightly randomized timesteps 1.0, 2.0, 3.0...
// healthy people are moved at slightly randomized timesteps 0.5, 1.5, 2.5, 3.5...
// this way we preserve the order of operation as in the original model
void ProcessEvent(lp_id_t me, simtime_t now, unsigned event_type, union event_t payload, unsigned int event_size, region_t *state)
{
	if(event_type != LP_INIT)
		state->now = now;

	switch(event_type) {
		case LP_INIT:
			(void) event_size;
			// standard stuff
			region_t *region = rs_malloc(sizeof(region_t));
			memset(region, 0, sizeof(*region));
			SetState(region);

#if MANUAL_MODE > 0
			state = region;
#else
			ApproximatedModeSwitch(EXEC_MODE);
#endif

			srand48_r(Random() * INT_MAX, &(region->rng_data));

			// initialize lists
			int j = END_STATES;
			while (j--) {
				guy_init_list(&(region->agents[j]));
			}

			if (!me) {
				// this function let LP0 coordinate the init phase
				guy_init(&region->rng_data);
			}
			unsigned phase = 0;
			ScheduleNewEvent(me, (conf.termination_time - 1) / GATHER_STATS_COUNT + now, GATHER_STATS, &phase,
							 sizeof(phase));
			break;

		case INFECTION:
			guy_on_infection(payload.i_m, state);
			break;

		case GUY_RECV:
			guy_recv(me, payload.agents, event_size, state);
			break;

		case GUY_MOVE:
			guy_move(me, state);
			break;

		case GUY_INIT:
			guy_on_init(payload.in_m, state);
			guy_move(me, state);
			break;

		case GATHER_STATS:;
			simtime_t step = (conf.termination_time - 1) / GATHER_STATS_COUNT;

			unsigned this_phase = *payload.phase;
			memcpy(state->stats_agents_count[this_phase], state->agents_count, sizeof(state->agents_count));
			++this_phase;
			ScheduleNewEvent(me, step + now, GATHER_STATS, &this_phase, sizeof(this_phase));
			break;

		case LP_FINI:;
			static unsigned stats[GATHER_STATS_COUNT][END_STATES] = {0};
			for (unsigned i = 0; i < GATHER_STATS_COUNT; ++i)
				for (int k = 0; k < END_STATES; ++k)
					stats[i][k] += state->stats_agents_count[i][k];

			if (me != NUM_LPS - 1)
				return;

			FILE *f = fopen("tbc_stats.txt", "w");
			for (unsigned i = 0; i < GATHER_STATS_COUNT; ++i) {
				for (int k = 0; k < END_STATES; ++k)
					fprintf(f, "%u ", stats[i][k]);
				fprintf(f, "\n");
			}
			return;

		default:
			printf("%s:%d: Unsupported event: %d\n", __FILE__, __LINE__, event_type);
			exit(EXIT_FAILURE);
	}
#if MANUAL_MODE > 0
	int j = END_STATES;
	unsigned t = 0;
	while (j--) {
		t += state->agents_count[j];
	}
#endif
#if MANUAL_MODE == 1
	ApproximatedModeSwitch(
			2 * state->agents_count[PRECISE_STATE] > t ? APPROXIMATED_MODE_PRECISE : APPROXIMATED_MODE_APPROXIMATED);
#elif MANUAL_MODE == 2
	ApproximatedModeSwitch(
			2 * state->agents_count[PRECISE_STATE] < t ? APPROXIMATED_MODE_PRECISE : APPROXIMATED_MODE_APPROXIMATED);
#endif
}

bool CanEnd(lp_id_t me, const void *snapshot)
{
	(void) me;
	(void) snapshot;
	return false;
}

void RestoreApproximated(lp_id_t me, void *ptr) {
	(void) me;
	region_t *region = ptr;
	init_t init_data;
	memcpy(init_data.agents_count, region->agents_count, sizeof(region->agents_count));
	int j = END_STATES;
	while (j--) {
		if (j == PRECISE_STATE)
			continue;
		region->agents_count[j] = 0;
		region->agents[j].next = NULL;
		region->agents[j].prev = NULL;
	}
	init_data.agents_count[PRECISE_STATE] = 0;
	guy_on_init(&init_data, region);
}

struct topology *topology;

int main(void) {
	topology = InitializeTopology(TOPOLOGY_SQUARE, (unsigned) sqrt(NUM_LPS), (unsigned) sqrt(NUM_LPS));
	conf.prng_seed = time(NULL);
	RootsimInit(&conf);
	return RootsimRun();
}
