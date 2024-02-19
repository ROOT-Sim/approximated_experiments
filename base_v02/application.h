#include "ROOT-Sim.h"

#define MAX_BUFFERS 1000
#define MAX_BUFFER_SIZE 1024
#define TAU 1.5
#define SEND_PROBABILITY 0.05
#define ALLOC_PROBABILITY 0.2
#define DEALLOC_PROBABILITY 0.2

// Event types
enum {
	LOOP,
	RECEIVE
};

#define COMPLETE_EVENTS 10000	// for the LOOP traditional case

// This structure defines buffers lists
typedef struct _buffer {
	double value; //synthetic data array
	unsigned char abs_sentinel;
	unsigned char rel_sentinel;
} buffer;

// LP simulation state
typedef struct _lp_state_type {
	unsigned int events;
	unsigned buffer_count;
	unsigned total_checksum;
	double ts[COMPLETE_EVENTS];
	double precise_values[COMPLETE_EVENTS];
	double abs_approx_values[COMPLETE_EVENTS];
	double rel_approx_values[COMPLETE_EVENTS];
	buffer *precise;
	buffer *abs_approx;
	buffer *rel_approx;
} lp_state_type;

buffer* get_buffer(buffer *head, unsigned i);
unsigned read_buffer(buffer *head, unsigned i); //reads synthetic data and performs stupid hash
buffer* allocate_buffer(buffer *head, const unsigned *data, unsigned count); //allocates a buffer with @count of elements, initialized with content of @data.
buffer* deallocate_buffer(buffer *head, unsigned i); //deallocate buffer at pos i



