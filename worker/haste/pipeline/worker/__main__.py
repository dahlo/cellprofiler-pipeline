import argparse

import pika
from pika import PlainCredentials
from sys import argv

ARG_PARSE_PROG_NAME = 'python3 -u -m haste.pipeline.worker'


def parse_args():
    parser = argparse.ArgumentParser(description='Watch directory and stream new files to HASTE',
                                     prog=ARG_PARSE_PROG_NAME)

    # parser.add_argument('--include', type=str, nargs='?', help='include only files with this extension')
    # parser.add_argument('--tag', type=str, nargs='?', help='short ASCII tag to identify this machine (e.g. ben-laptop)')
    parser.add_argument('--host', type=str, nargs='?', help='Hostname for RabbitMQ', default='localhost')
    # parser.add_argument('--username', type=str, nargs='?', help='Username for HASTE')
    # parser.add_argument('--password', type=str, nargs='?', help='Password for HASTE')
    #
    # parser.add_argument('--x-preprocessing-cores', default=1, type=int)
    # parser.add_argument('--x-mode', default=1, type=int)
    # parser.set_defaults(prio=True)

    parser.add_argument('path', metavar='path', type=str, nargs=1, help='path to watch (e.g. C:/docs/foo')

    args = parser.parse_args()
    return args



def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)


if __name__ == '__main__':
    args = parse_args()

    path = args.path
    # include = args.include
    # tag = args.tag
    cli_rabbitmq_host = args.host

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(cli_rabbitmq_host, credentials=PlainCredentials('guest', 'guest')))
    channel = connection.channel()

    channel.queue_declare(queue='files')

    channel.basic_consume(queue='files',
                          auto_ack=True, # TODO: only ack when processed
                          on_message_callback=callback)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

