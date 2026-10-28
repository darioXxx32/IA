
CC=gcc
CFLAGS=
LDFLAGS=-lrabbitmq

all: c_producer c_consumer

c_producer: c_producer.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

c_consumer: c_consumer.c
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS)

clean:
	rm -f c_producer c_consumer
