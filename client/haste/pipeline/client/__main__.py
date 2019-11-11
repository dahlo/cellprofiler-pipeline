import argparse
import datetime
import os
import logging
import pika
import time
from pika import PlainCredentials
from sys import argv

from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import PatternMatchingEventHandler

ARG_PARSE_PROG_NAME = 'python3 -u -m haste.pipeline.client'
PAUSE_SECS = 5

LOGGING_LEVEL = logging.INFO
LOGGING_FORMAT_DATE = '%Y-%m-%d %H:%M:%S.%d3'
LOGGING_FORMAT = '%(asctime)s - AGENT - %(threadName)s - %(levelname)s - %(message)s'

# TODO
def create_stream_id(stream_id_tag):
    stream_id = datetime.datetime.today().strftime('%Y_%m_%d__%H_%M_%S') + '_' + stream_id_tag
    return stream_id



def parse_args():
    parser = argparse.ArgumentParser(description='Watch directory and stream new files to HASTE',
                                     prog=ARG_PARSE_PROG_NAME)

    parser.add_argument('--include', type=str, nargs='?', help='include only files with this extension(s). Comma separated if multiple. Ex: .jpg,.jpeg,.png', default=['*'])
    parser.add_argument('--tag', type=str, nargs='?', help='short ASCII tag to identify this machine (e.g. ben-laptop)', default="")
    parser.add_argument('--host', type=str, nargs='?', help='Hostname for RabbitMQ', default='localhost')
    parser.add_argument('--username', type=str, nargs='?', help='Username for AMPQ', default='guest')
    parser.add_argument('--password', type=str, nargs='?', help='Password for AMPQ', default='guest')
    #
    # parser.add_argument('--x-preprocessing-cores', default=1, type=int)
    # parser.add_argument('--x-mode', default=1, type=int)
    # parser.set_defaults(prio=True)

    parser.add_argument('path', metavar='path', type=str, nargs=1, help='path to watch (e.g. C:/docs/foo')

    args = parser.parse_args()
    return args
    
    
# file watcher events
# def on_deleted(event):
# def on_modified(event):
# def on_moved(event):
def on_created(event):
    
    # wait until the file size has stopped changing
    # file_size = -1
    # while file_size != os.path.getsize(event.src_path):
        # file_size = os.path.getsize(event.src_path)
        # time.sleep(1)
        
    global filenames_previous, args
        
    # skip if the file has been seen before
    if event.src_path in filenames_previous:
        return
        
    body = event.src_path

    # TODO: some encoding issue here?! -- use strings
    hdrs = {"tag": tag,
            "timestamp": str(time.time()),
            "path": str(path),
            "stream_id": stream_id}
    properties = pika.BasicProperties(app_id='haste.pipeline.client',
                                      content_type='application/json',
                                      headers=hdrs)
    
    # publish the message
    publish_rmq(queue='files', properties=properties, body=body)
                          
    # remember the file
    filenames_previous.add(event.src_path)
    logging.info(f"Sent {body}")
    
    
# fuction to publish to RabbitMQ that will try to reconnect to the mq if timedout
def publish_rmq(queue, properties, body, exchange=''):
    
    global connection, channel
        
    try:
        channel.basic_publish(exchange=exchange,
                              routing_key=queue,
                              body=body,
                              properties=properties)
        
    # try reconnecting if the connection has timedout
    except pika.exceptions.StreamLostError:
        
        # reconnect
        logging.info(f'Reconneting to RabbitMQ server: {args.host} (excl. creds)')
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(args.host, credentials=PlainCredentials(args.username, args.password), heartbeat=0))
        channel = connection.channel()
        channel.queue_declare(queue=queue)
        
        # try publishing again
        channel.basic_publish(exchange=exchange,
                              routing_key=queue,
                              body=body,
                              properties=properties)



# a dummy object to be able to trick the event manager that a file has been triggered
class DummyEvent():
    pass


def main():
    logging.basicConfig(level=LOGGING_LEVEL,
                        format=LOGGING_FORMAT,
                        datefmt=LOGGING_FORMAT_DATE)
                        
    # readability
    global path, tag, channel, stream_id, filenames_previous, connection, channel, args
    args = parse_args()
    path = args.path[0]
    tag = args.tag
    rabbitmq_host = args.host
    stream_id = create_stream_id(tag)
    filenames_previous = set()
               
    # if multiple file endings
    include = args.include.split(',')
    
    # add star before the file ending if missing
    include = [ ext.lower() if ext.startswith('*') else "*"+ext.lower() for ext in include ]
    
    logging.info(f'starting with args {[path, include, tag, rabbitmq_host]} (excl. creds)')
    
    # create the event handler
    my_event_handler = PatternMatchingEventHandler(include, ignore_patterns="", ignore_directories=True, case_sensitive=False)
    my_event_handler.on_created = on_created
    # my_observer = Observer() # only on local file systems (inotify)
    my_observer = PollingObserver(timeout=20)
    my_observer.schedule(my_event_handler, path, recursive=False)
    
    # TODO: make queue persistent between rabbitMQ restarts?
    # connect to the RabbitMQ server
    logging.info(f'starting with args {[path, include, tag, rabbitmq_host]} (excl. creds)')
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(args.host, credentials=PlainCredentials(args.username, args.password), heartbeat=0))
    channel = connection.channel()
    channel.queue_declare(queue='files')

    logging.info('connected to AMPQ.')
    
    # trigger event for all existing files?
    existing_file_event = DummyEvent()
    for existing_file in os.listdir(path): # list dir
        if os.path.isfile(os.path.join(path, existing_file)): # only files
            if f'*{os.path.splitext(existing_file)[-1].lower()}' in include: # if extension is matching            
                existing_file_event.src_path = os.path.join(path, existing_file) # add property to dummy object to have the same structure as a watchdog even object
                on_created(existing_file_event) # manually trigger creation function
    
    # start monitoring
    my_observer.start()
    logging.info('started monitoring directory.')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()
        connection.close()


if __name__ == '__main__':
    main()
