import pika
from sys import argv


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)


if __name__ == '__main__':
    connection = pika.BlockingConnection(pika.ConnectionParameters(argv[1]))
    channel = connection.channel()

    channel.queue_declare(queue='files')

    channel.basic_consume(queue='files',
                          auto_ack=True, # TODO: only ack when processed
                          on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

