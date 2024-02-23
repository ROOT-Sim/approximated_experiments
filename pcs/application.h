#include <ROOT-Sim.h>

extern struct simulation_configuration conf;


#include "config.h"

#ifndef LOOKAHEAD
#define LOOKAHEAD 0.0
#endif

/* DISTRIBUZIONI TIMESTAMP */
#define UNIFORM		0
#define EXPONENTIAL	1


#define PARTITIONS 2
#define CELLS_PER_PARTITION  (conf.lps/PARTITIONS)

#define PERC_HOT 0.1
#define NUM_HOT_CELLS  ((unsigned int)(PERC_HOT*conf.lps))
#define TARGET_SKEW 0.7

#define MIN_LOAD_PARTITION	   (CELLS_PER_PARTITION/args.ta)
#define MAX_LOAD_PARTITION	   (MIN_LOAD_PARTITION*(1+TARGET_SKEW))

#define NUM_CLD_CELLS_IN_MAX ((conf.lps/PARTITIONS)-NUM_HOT_CELLS)
#define LOAD_FROM_CLD_CELLS  (NUM_CLD_CELLS_IN_MAX/args.ta)
#define LOAD_FROM_HOT_CELLS    (MAX_LOAD_PARTITION-LOAD_FROM_CLD_CELLS)
#define TA_HOT                 (NUM_HOT_CELLS/LOAD_FROM_HOT_CELLS)


#define max(x,y) ((x)>(y) ? (x) : (y))

#define CHANNELS_PER_HOT_CELL	(max((unsigned int)(args.ta_duration*1.1/TA_HOT), args.channels))



#define HANDOFF_SHIFT 0.000001

//#define PCS_STAT_FREQUENCY 10.0 //0.5

/* Channel states */
#define CHAN_BUSY	1
#define CHAN_FREE	0

/* EVENT TYPES - PCS */
#define START_CALL	20
#define END_CALL	21
#define HANDOFF_LEAVE	30
#define HANDOFF_RECV	31
#define FADING_RECHECK	40
#define GATHER_STATS	50

#define MSK 0x1
#define SET_CHANNEL_BIT(B,K) ( B |= (MSK << K) )
#define RESET_CHANNEL_BIT(B,K) ( B &= ~(MSK << K) )
#define CHECK_CHANNEL_BIT(B,K) ( B & (MSK << K) )

#define BITS (sizeof(int) * 8)

#define CHECK_CHANNEL(P,I) ( CHECK_CHANNEL_BIT(						\
	((unsigned int*)(((lp_state_type*)P)->channel_state))[(int)((int)I / BITS)],	\
	((int)I % BITS)) )
#define SET_CHANNEL(P,I) ( SET_CHANNEL_BIT(						\
	((unsigned int*)(((lp_state_type*)P)->channel_state))[(int)((int)I / BITS)],	\
	((int)I % BITS)) )
#define RESET_CHANNEL(P,I) ( RESET_CHANNEL_BIT(						\
	((unsigned int*)(((lp_state_type*)P)->channel_state))[(int)((int)I / BITS)],	\
	((int)I % BITS)) )

// Message exchanged among LPs
typedef struct _event_content_type {
	int cell; // The destination cell of an event
	unsigned int from; // The sender of the event (in case of HANDOFF_RECV)
	simtime_t sent_at; // Simulation time at which the call was handed off
	simtime_t   call_term_time; // Termination time of the call (used mainly in HANDOFF_RECV)
	int *dummy;
	unsigned short channel; // Channel to be freed in case of END_CALL
} event_content_type;

#define CROSS_PATH_GAIN		0.00000000000005
#define PATH_GAIN		0.0000000001
#define MIN_POWER		3
#define MAX_POWER		3000
#define SIR_AIM			10

// Taglia di 16 byte
typedef struct _sir_data_per_cell{
   // double pad[40];
    double fading; // Fading of the call
    double power; // Power allocated to the call
} sir_data_per_cell;


#define POWER_SENTINEL_BITS  10
#define FADING_SENTINEL_BITS 6

#define PACK_SENTINEL(f,p)  ((f<<POWER_SENTINEL_BITS) | p)

#define FADING_PRECISE_THRESHOLD 	2.55
#define FADING_TARGET_ABS_ERROR 0.01

#define POWER_TARGET_REL_ERROR  0.02

#define COMPRESS_FADING(f) ( (unsigned char)((f)/(FADING_TARGET_ABS_ERROR*2.0)) )
#define EXTRACT_FADING(sf) ( FADING_TARGET_ABS_ERROR + ((double)sf)*FADING_TARGET_ABS_ERROR*2.0)


extern __thread double precomputed_table[256];
extern __thread int precomputed_table_done;


static inline unsigned char compress_power(double p){
	if(!precomputed_table_done){
        precomputed_table_done = 1;
        double th_val = MAX_POWER*(1-POWER_TARGET_REL_ERROR)/(1+POWER_TARGET_REL_ERROR);
        for(int i =0;i<256;i++){
            precomputed_table[i] = th_val;
            th_val *= (1-POWER_TARGET_REL_ERROR)/(1+POWER_TARGET_REL_ERROR);
        }
    }
    unsigned char sentinel = 0;
	double th_val = (1-POWER_TARGET_REL_ERROR)/(1+POWER_TARGET_REL_ERROR);
	double pr_val = p;
	//double cur_val = MAX_POWER*th_val;
    double cur_val = precomputed_table[sentinel];
	while(cur_val > pr_val){
		//cur_val *= th_val;
		sentinel++;
cur_val =        precomputed_table[sentinel];
	}
	return sentinel;
}

static inline double extract_power(unsigned char sp){
	double p = MAX_POWER*(1-POWER_TARGET_REL_ERROR)/(1+POWER_TARGET_REL_ERROR);
	//for(unsigned char i = 0;i<sp;i++)
	//	p *= (1-POWER_TARGET_REL_ERROR)/(1+POWER_TARGET_REL_ERROR);
p = precomputed_table[sp];
	p *= (1+POWER_TARGET_REL_ERROR);
	return p;
}

// Taglia di 16 byte
typedef struct _channel{
	unsigned short channel_id; // Number of the channel
	unsigned char fad_sen;
	unsigned char pow_sen;
	sir_data_per_cell *sir_data; // Signal/Interference Ratio data
	struct _channel *next;
	struct _channel *prev;
} channel;


typedef struct channel_log{
    sir_data_per_cell *sir_data;
	unsigned char fad_sen;
	unsigned char pow_sen;  
unsigned short id;
} channel_log_t;

typedef struct _lp_state_type{
	int ecs_count;

	unsigned int channel_counter; // How many channels are currently free
	unsigned int arriving_calls; // How many calls have been delivered within this cell
	unsigned int complete_calls; // Number of calls which were completed within this cell
	unsigned int blocked_on_setup; // Number of calls blocked due to lack of free channels
	unsigned int blocked_on_handoff; // Number of calls blocked due to lack of free channels in HANDOFF_RECV
	unsigned int leaving_handoffs; // How many calls were diverted to a different cell
	unsigned int arriving_handoffs; // How many calls were received from other cells
	unsigned int cont_no_sir_aim; // Used for fading recheck
	unsigned int executed_events; // Total number of events
	unsigned int used_log_entryused_log_entry;

unsigned long long start_ts;

	simtime_t lvt; // Last executed event was at this simulation time

	double ta; // Current call interarrival frequency for this cell
	double ref_ta; // Initial call interarrival frequency (same for all cells)
	double ta_duration; // Average duration of a call
	double ta_change; // Average time after which a call is diverted to another cell
	double fading_recheck_time;

	int channels_per_cell; // Total channels in this cell
	int total_calls;

	bool check_fading; // Is the model set up to periodically recompute the fading of all ongoing calls?
	bool fading_recheck;
	bool variable_ta; // Should the call interarrival frequency change depending on the current time?

	int rounds;
    unsigned int *channel_state;
	struct _channel *channels;
	channel_log_t **channel_logs;
	int channel_log_epoch;
    int dummy;
	bool dummy_flag;

} lp_state_type;


double recompute_ta(double ref_ta, simtime_t now);
double generate_cross_path_gain(void);
double generate_path_gain(void);
void deallocation(unsigned int lp, lp_state_type *state, int channel, simtime_t);
int allocation(lp_state_type *state);
void fading_recheck(lp_state_type *pointer);


extern int channels_per_cell;


