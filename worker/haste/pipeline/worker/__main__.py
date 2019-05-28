import argparse
import logging
import os
import tempfile
from tempfile import NamedTemporaryFile
import json

import csv
import pika
import time
from haste_storage_client.core import HasteStorageClient
from pika import PlainCredentials
from sys import argv
import subprocess
import shutil

ARG_PARSE_PROG_NAME = 'python2 -u -m haste.pipeline.worker'
PAUSE_SECS = 5

LOGGING_LEVEL = logging.DEBUG
LOGGING_FORMAT_DATE = '%Y-%m-%d %H:%M:%S.%d3'
LOGGING_FORMAT = '%(asctime)s - AGENT - %(threadName)s - %(levelname)s - %(message)s'

# Default config for dev purposes.
DEFAULT_SOURCE_DIR = "/Users/benblamey/projects/haste/haste-desktop-agent-images/target/"
DEFAULT_TARGET_DIR = "/Users/benblamey/projects/haste/haste-desktop-agent-images/hsc_tiers/"
DEFAULT_CONFIG = {
    "configs": [
        {
            "tag": "foo",
            "root_path": "/Users/benblamey/projects/haste/haste-desktop-agent-images/target/",
            "pipeline": "/Users/benblamey/projects/haste/cell-profiler-work/OutOfFocus-TestImages.cppipe",
            # range 0..8. 0 = focussed, 8 = unfocused.
            "interestingness_function": "lambda row: 1 - float(row['ImageFocus_Score_myimages']) / 8",
            "storage_policy": "[ [0.0, 0.199999999, \"move-to-trash\"], [0.2, 1.0, \"move-to-keep\"] ]",
            "haste_storage_client_config": {
                "haste_metadata_server": {
                    # In K8, this is the service name (since we're in the same namespace'
                    "connection_string": "mongodb://localhost:27017/streams"
                    # "connection_string": "mongodb://mongodb.haste.svc.cluster:27017/streams"
                },
                "log_level": "DEBUG",
                "targets": [
                    {
                        "id": "move-to-keep",
                        "class": "haste_storage_client.storage.storage.MoveToDir",
                        "config": {
                            "source_dir": DEFAULT_SOURCE_DIR,
                            "target_dir": DEFAULT_TARGET_DIR + 'keep/'
                        }
                    },
                    # For a PoC, trash is simply another dir:
                    {
                        "id": "move-to-trash",
                        "class": "haste_storage_client.storage.storage.MoveToDir",
                        "config": {
                            "source_dir": DEFAULT_SOURCE_DIR,
                            "target_dir": DEFAULT_TARGET_DIR + 'trash/'
                        }
                    }
                ]
            }
        }
    ]
}

haste_storage_clients_by_stream_id = {}


class PreComputedInterestingnessModel:

    def interestingness(self,
                        stream_id=None,
                        timestamp=None,
                        location=None,
                        substream_id=None,
                        metadata=None,
                        mongo_collection=None):
        """
        :param stream_id (str): ID for the stream session - used to group all the data for that streaming session.
        :param timestamp (numeric): should come from the cloud edge (eg. microscope). integer or floating point.
            *Uniquely identifies the document within the streaming session*.
        :param location (tuple): spatial information (eg. (x,y)).
        :param substream_id (string): ID for grouping of documents in stream (eg. microscopy well ID), or 'None'.
        :param metadata (dict): extracted metadata (eg. image features).
        :param mongo_collection: collection in mongoDB allowing custom queries (this is a hack - best avoided!)
        """
        return {'interestingness': metadata['interestingness']}


def parse_args():
    parser = argparse.ArgumentParser(description='Watch directory and stream new files to HASTE',
                                     prog=ARG_PARSE_PROG_NAME)

    # parser.add_argument('--include', type=str, nargs='?', help='include only files with this extension')
    # parser.add_argument('--tag', type=str, nargs='?', help='short ASCII tag to identify this machine (e.g. ben-laptop)')
    parser.add_argument('--host', type=str, nargs='?', help='Hostname for AMPQ (eg. RabbitMQ)', default='localhost')
    parser.add_argument('--username', type=str, nargs='?', help='Username for AMPQ', default='guest')
    parser.add_argument('--password', type=str, nargs='?', help='Password for AMPQ', default='guest')
    parser.add_argument('--config', type=str, nargs='?', help='configuration in JSON',
                        default=json.dumps(DEFAULT_CONFIG))
    #
    # parser.add_argument('--x-preprocessing-cores', default=1, type=int)
    # parser.add_argument('--x-mode', default=1, type=int)
    # parser.set_defaults(prio=True)

    # parser.add_argument('path', metavar='path', type=str, nargs=1, help='path to watch (e.g. C:/docs/foo)')

    args = parser.parse_args()
    return args


def callback(ch, method, properties, body):
    # ch: blocking channel
    # body -- in bytes
    # properties -- BasicProperties   call .headers -> dict

    filename = body.decode('utf-8')  # TODO: hmmm... maybe this is ASCII? nm.
    headers = properties.headers
    logging.info('received: {} {}'.format(body, headers))
    delivery_tag = method.delivery_tag

    acked = False

    try:
        run_cp(filename, headers)

        # if we got here without an exception, ack the message.]
        ch.basic_ack(delivery_tag)
        acked = True
    finally:
        if not acked:
            # re-queue -- beware infinite loop...
            ch.basic_nack(delivery_tag, requeue=True)


def run_cp(filename, headers):
    tag = headers['tag']
    stream_id = headers['stream_id']
    config_for_tag = get_config_for_tag(tag)
    image_file_path = os.path.join(config_for_tag['root_path'], filename)
    image_input_file_list_path = create_data_file_list(image_file_path)
    cellprofiler_output_dir = tempfile.mkdtemp()  # make a new temp dir

    if not os.path.exists(image_file_path):
        # Incase the client has been restarted, and the file already moved, it will no longer exist.
        logging.warn("image path doesnt exist: {} -- will ACK message".format(image_input_file_list_path))
        return

    # cellprofiler_output_dir = cellprofiler_output_dir.name
    try:
        # See: https://github.com/CellProfiler/CellProfiler/wiki/Adapting-CellProfiler-to-a-LIMS-environment#cmd

        params = [
            # "echo",
            "python2",
            "-m",
            "cellprofiler",
            "-c",  # run headless.

            # "--plugins-directory",
            # "/users/benblamey/projects/haste/CellProfiler-plugins",
            # "/CellProfiler-plugins",

            "--file-list",
            image_input_file_list_path,

            "-p",
            config_for_tag['pipeline'],

            "-o",
            cellprofiler_output_dir,

        ]
        logging.debug("params: {}".format(params))

        exit_code = subprocess.call(params)

        logging.debug('exit code from cellprofiler wad {}'.format(exit_code))

        # exlude the possibility of a race condition when reading back the output files.
        time.sleep(1)

        # read the output
        output_files = os.listdir(cellprofiler_output_dir)

        output_file_image_csv = find_output_file(output_files)

        output_file_image_csv_path = os.path.join(cellprofiler_output_dir, output_file_image_csv)

        row_lambda = eval(config_for_tag['interestingness_function'])

        interestingness = None

        metadata = {}
        metadata.update(headers)

        # This is 'magic' metadata -- its read by the 'MoveToDir' storage target.
        metadata['original_filename'] = filename

        with open(output_file_image_csv_path, 'r') as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                interestingness = row_lambda(row)
                logging.info("interestingness for file: {} is: {}".format(image_file_path, interestingness))
                metadata['cellprofiler_output'] = row
                # TODO: save the metadata from the other CSV file
                break

        if interestingness is None:
            raise Exception('interestingness was None - terminating.')

        metadata['interestingness'] = interestingness

        if stream_id in haste_storage_clients_by_stream_id:
            hsc = haste_storage_clients_by_stream_id[stream_id]
        else:
            model = PreComputedInterestingnessModel()
            hsc = HasteStorageClient(
                stream_id,
                config=config_for_tag['haste_storage_client_config'],
                interestingness_model=model,
                storage_policy=[tuple(p) for p in
                                json.loads(config_for_tag['storage_policy'])])  # convert lists to tuples
            haste_storage_clients_by_stream_id[tag] = hsc

        hsc.save(
            timestamp=time.time(),  # TODO
            location=(0, 0),  # TODO
            substream_id=None,
            blob_bytes=b'',  # we're just moving the file -- leave this empty
            metadata=metadata)

        # logging.debug("output _Image.csv: \n{}".format(fin.read()))

        # input()

    finally:
        # TODO: turn this back on -- otherwise old dirs will fill up.
        # os.unlink(image_input_file_list_path)
        # shutil.rmtree(cellprofiler_output_dir)
        pass


def find_output_file(output_files):
    logging.debug("output filenames: {}".format(output_files))
    for output_file in output_files:
        if output_file.endswith("_Image.csv"):
            return output_file
    raise Exception("could not find output file {}".format(output_files))


def get_config_for_tag(tag):
    print(config)
    for c in config["configs"]:
        if c['tag'] == tag:
            return c
    raise Exception('no config for tag {}'.format(tag))


def create_data_file_list(image_file_path):
    import tempfile

    fp = tempfile.TemporaryFile()

    f = NamedTemporaryFile(delete=False)
    logging.debug('created temp data file {}'.format(f.name))
    # '/tmp/tmptjujjt'
    # f.write("Image_PathName\n{}\n".format(image_file_path).encode("utf-8"))
    f.write(image_file_path.encode("utf-8"))
    # 13
    f.close()

    return f.name


def main():
    global config

    # input()

    logging.basicConfig(level=LOGGING_LEVEL,
                        format=LOGGING_FORMAT,
                        datefmt=LOGGING_FORMAT_DATE)

    args = parse_args()
    # path = args.path
    # include = args.include
    # tag = args.tag
    ampq_host = args.host

    config = json.loads(args.config)

    logging.info('starting with args {} (excl. creds)'.format([ampq_host, config]))
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(ampq_host, credentials=PlainCredentials(args.username, args.password)))
    channel = connection.channel()
    channel.queue_declare(queue='files')
    channel.basic_qos(prefetch_count=1)  # max 1 unacked message at time
    channel.basic_consume(queue='files',
                          auto_ack=False,  # only ack when processed successfully 
                          on_message_callback=callback)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == '__main__':
    main()
