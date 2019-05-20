import pika
from sys import argv


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)



if __name__ == '__main__':
    connection = pika.BlockingConnection(pika.ConnectionParameters(argv[1]))
    channel = connection.channel()

    channel.queue_declare(queue='files')

    channel.basic_publish(exchange='',
                          routing_key='files',
                          body='Hello World!')
    print(" [x] Sent 'Hello World!'")

    connection.close()

