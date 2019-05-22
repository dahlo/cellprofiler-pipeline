import argparse
import os
import logging
import pika
import time
from pika import PlainCredentials
from sys import argv

ARG_PARSE_PROG_NAME = 'python3 -u -m haste.pipeline.client'
PAUSE_SECS = 5

LOGGING_LEVEL = logging.INFO
LOGGING_FORMAT_DATE = '%Y-%m-%d %H:%M:%S.%d3'
LOGGING_FORMAT = '%(asctime)s - AGENT - %(threadName)s - %(levelname)s - %(message)s'


def parse_args():
    parser = argparse.ArgumentParser(description='Watch directory and stream new files to HASTE',
                                     prog=ARG_PARSE_PROG_NAME)

    parser.add_argument('--include', type=str, nargs='?', help='include only files with this extension')
    parser.add_argument('--tag', type=str, nargs='?', help='short ASCII tag to identify this machine (e.g. ben-laptop)')
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


def main():
    logging.basicConfig(level=LOGGING_LEVEL,
                        format=LOGGING_FORMAT,
                        datefmt=LOGGING_FORMAT_DATE)

    global include, filenames_previous
    args = parse_args()
    path = args.path[0]
    include = args.include
    if not include.startswith('.'):
        include = '.' + include
    tag = args.tag
    rabbitmq_host = args.host

    logging.info(f'starting with args {[path, include, tag, rabbitmq_host]} (excl. creds)')


    connection = pika.BlockingConnection(
        pika.ConnectionParameters(rabbitmq_host, credentials=PlainCredentials('guest', 'guest')))
    channel = connection.channel()
    channel.queue_declare(queue='files')

    logging.info('connected to AMPQ.')


    try:
        filenames_previous = set()

        while True:
            time_start = time.time()

            logging.info(f'starting dir listing of {path}')

            filenames = os.listdir(path)

            filenames = list(filter(lambda filename: filename.endswith(include), filenames))

            logging.debug(filenames)

            filenames = list(filter(lambda filename: filename not in filenames_previous, filenames))

            if len(filenames) == 0:
                logging.info('no new files found.')

            for filename in filenames:
                # body = f'Hello World! {time.time()}'
                body = filename

                # TODO: some encoding issue here?! -- use strings
                hdrs = {"tag": tag,
                        "timestamp": str(time_start),
                        "path": str(path)}
                properties = pika.BasicProperties(app_id='haste.pipeline.client',
                                                  content_type='application/json',
                                                  headers=hdrs)


                channel.basic_publish(exchange='',
                                      routing_key='files',
                                      body=body,
                                      properties=properties)
                logging.info(f"Sent {body}")

            pause = (time_start + 5) - time.time()

            if pause < 0:
                logging.warn(f'dir listing overran by {-pause} seconds')
            else:
                time.sleep(pause)

            filenames_previous = set(filenames)

    finally:
        connection.close()


if __name__ == '__main__':
    main()
