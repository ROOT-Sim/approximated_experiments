/*
 * application.h
 *
 *  Created on: 20 lug 2018
 *      Author: andrea
 */

#ifndef MODELS_TUBERCOLOSIS_APPLICATION_H_
#define MODELS_TUBERCOLOSIS_APPLICATION_H_

#include <ROOT-Sim.h>
#include "guy.h"

enum {
	INFECTION,
	GUY_INIT,
	GUY_MOVE,
	GUY_RECV,
};

extern struct topology *topology;

// this samples a random number with binomial distribution TODO could be useful in the numeric library
extern unsigned random_binomial(unsigned trials, double p, struct drand48_data *rng_state);

struct guy_t *init_guy(region_t *, enum agent_state);
#endif /* MODELS_TUBERCOLOSIS_APPLICATION_H_ */
