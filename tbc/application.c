#include "application.h"
#include "config.h"
#include "parameters.h"
#include "guy.h"
#include "guy_init.h"

#include <math.h>
#include <stdio.h>

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
};

extern void ProcessEvent(lp_id_t me, simtime_t now, unsigned event_type, union event_t event_content, unsigned int event_size, region_t *state);
extern bool CanEnd(lp_id_t me, const void *snapshot);
extern void RestoreApproximated(lp_id_t id, void *ptr);

struct simulation_configuration conf = {
    .lps = NUM_LPS,
    .n_threads = NUM_THREADS,
    .termination_time = 1000,
    .gvt_period = 100000,
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

			region->me = me;

			srand48_r(Random() * INT_MAX, &(region->random_initialization_buf));

			// initialize lists
			int j = END_STATES;
			while (j--) {
				guy_init_list(&(region->agents[j]));
			}

			if(!me) {
				// this function let LP0 coordinate the init phase
				guy_init(&region->random_initialization_buf);
			}

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

		case LP_FINI:
			break;

		default:
			printf("%s:%d: Unsupported event: %d\n", __FILE__, __LINE__, event_type);
			exit(EXIT_FAILURE);
	}

}

bool CanEnd(lp_id_t me, const void *snapshot)
{
	(void) me;
	(void) snapshot;
	return false;
}

void RestoreApproximated(lp_id_t me, void *ptr)
{
	(void) me;
	region_t *region = ptr;
	init_t init_data;
	memcpy(init_data.agents_count, region->agents_count, sizeof(region->agents_count));
	int j = END_STATES;
	while (j--) {
		if (j == HEALTHY)
			continue;
		region->agents_count[j] = 0;
		region->agents[j].next = NULL;
		region->agents[j].prev = NULL;
	}
	init_data.agents_count[HEALTHY] = 0;
	guy_on_init(&init_data, region);
}

struct topology *topology;

int main(void)
{
	topology = InitializeTopology(TOPOLOGY_SQUARE, (unsigned)sqrt(NUM_LPS), (unsigned)sqrt(NUM_LPS));
	RootsimInit(&conf);
	return RootsimRun();
}
