
/* c_consumer.c */
#include <amqp.h>
#include <amqp_tcp_socket.h>
#include <amqp_framing.h>
#include <stdio.h>
#include <stdlib.h>

static const char *broker_host(void) {
  const char *host = getenv("RABBITMQ_HOST");
  return (host && *host) ? host : "localhost";
}

int main(void) {
  const char *hostname = broker_host();
  int port = 5672;
  const char *queue = "hello";

  amqp_connection_state_t conn = amqp_new_connection();
  amqp_socket_t *socket = amqp_tcp_socket_new(conn);
  if (!socket) { fprintf(stderr, "Socket error\n"); return 1; }
  if (amqp_socket_open(socket, hostname, port)) { fprintf(stderr, "Open socket error\n"); return 1; }

  amqp_rpc_reply_t login = amqp_login(conn, "/", 0, 131072, 0,
                                      AMQP_SASL_METHOD_PLAIN, "guest", "guest");
  if (login.reply_type != AMQP_RESPONSE_NORMAL) {
    fprintf(stderr, "RabbitMQ login failed (reply type %d)\n", login.reply_type);
    amqp_destroy_connection(conn);
    return 1;
  }
  amqp_channel_open(conn, 1);
  if (amqp_get_rpc_reply(conn).reply_type != AMQP_RESPONSE_NORMAL) {
    fprintf(stderr, "Channel open failed\n");
    amqp_connection_close(conn, AMQP_REPLY_SUCCESS);
    amqp_destroy_connection(conn);
    return 1;
  }

  amqp_queue_declare_ok_t *r = amqp_queue_declare(conn, 1, amqp_cstring_bytes(queue),
      1, 0, 0, 0, amqp_empty_table);
  if (!r || amqp_get_rpc_reply(conn).reply_type != AMQP_RESPONSE_NORMAL) {
    fprintf(stderr, "Queue declaration failed\n");
    amqp_channel_close(conn, 1, AMQP_REPLY_SUCCESS);
    amqp_connection_close(conn, AMQP_REPLY_SUCCESS);
    amqp_destroy_connection(conn);
    return 1;
  }

  amqp_basic_consume(conn, 1, amqp_cstring_bytes(queue), amqp_empty_bytes, 0, 0, 0, amqp_empty_table);

  printf(" [*] Waiting for messages. Ctrl+C to exit.\n");
  while (1) {
    amqp_rpc_reply_t res;
    amqp_envelope_t envelope;

    amqp_maybe_release_buffers(conn);
    res = amqp_consume_message(conn, &envelope, NULL, 0);
    if (AMQP_RESPONSE_NORMAL != res.reply_type) break;

    printf(" [x] Received: %.*s\n",
           (int)envelope.message.body.len,
           (char *)envelope.message.body.bytes);

    amqp_basic_ack(conn, 1, envelope.delivery_tag, 0);
    amqp_destroy_envelope(&envelope);
  }

  amqp_channel_close(conn, 1, AMQP_REPLY_SUCCESS);
  amqp_connection_close(conn, AMQP_REPLY_SUCCESS);
  amqp_destroy_connection(conn);
  return 0;
}
