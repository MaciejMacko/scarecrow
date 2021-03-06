# import libraries
from vidgear.gears import VideoGear
from vidgear.gears import NetGear

from utilities.utils import *
from plugin_base.utils import *

import argparse
import configparser
import time

from utilities.utils import get_logger
logger = get_logger()


def run_camera(input_str, address, port, protocol, pattern=0, fps=25):
    """Runs the camera, sends messages

    Args:
        input_str (str): Path to video file **OR** an `int` for camera input
        address (str): URL of `OpenCV` server 
        port (int): Port of `OpenCV` server
        protocol (str): Protocol of of `OpenCV` server 
        pattern (int, optional): ZMQ Pattern. 0=`zmq.PAIR`, 1=`zmq.REQ/zmq.REP`; 2=`zmq.PUB,zmq.SUB`. Defaults to 0.
        fps (int, optional): Framerate for video capture. Defaults to 25.
    """
    if input_str.isdigit():
        input = int(input_str)
    else:
        input = input_str

    # Open any video stream; `framerate` here is just for picamera
    stream = VideoGear(source=input, framerate=fps).start()
    # server = NetGear() # Locally
    server = NetGear(address=address, port=port, protocol=protocol,
                     pattern=pattern, receive_mode=False, logging=True)

    # infinite loop until [Ctrl+C] is pressed
    while True:
        try:
            frame = stream.read()
            # check if frame is None
            if frame is None:
                logger.error('No frame available')
                break

            # send frame to server
            server.send(frame)

        except KeyboardInterrupt:
            # break the infinite loop
            break

    # safely close video stream
    stream.stop()


if __name__ == "__main__":
    # Args
    parser = argparse.ArgumentParser(description='Runs local image detection')
    parser.add_argument('--input', '-i', dest='in_file', type=str, required=True, default=0,
                        help='Input file (0 for webcam)')
    parser.add_argument('--config', '-c', dest='conf_path', type=str, required=False,
                        help='Path to config dir')
    args = parser.parse_args()
    # Conf
    conf = configparser.ConfigParser()
    conf_path = args.conf_path
    if conf_path is None:
        conf_path = os.path.join(os.path.abspath(
            os.path.dirname(__file__)), '../conf/')
        conf_path_core = '{}{}'.format(conf_path, 'config.ini')
        logger.warning('No conf path, using {}'.format(conf_path_core))
        conf.read(conf_path_core)
    else:
        conf.read('{}/config.ini'.format(conf_path))

    # Plugin ZMQ threads
    start_receiver_plugins(load_plugins(
        conf['Plugins']['Enabled'].split(','), conf_path=conf_path+'plugins.d'))

    logger.info('Starting camera stream')
    run_camera(args.in_file, conf['ZmqServer']['IP'], conf['ZmqServer']['Port'], conf['ZmqServer']['Protocol'],
               int(conf['ZmqServer']['Pattern']), int(conf['Video']['FPS']))
