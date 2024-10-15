

import logging
from .drivers.serialport import SerialDriver
from .tests.throughput import ThroughputTest

logging.basicConfig(level=logging.INFO)


def run_throughput_test(url, baudrate=1000000, timeout=10):
    with SerialDriver(url=url, baudrate=baudrate, timeout=timeout) as link:
        test = ThroughputTest(link)   
        try:
            result = test.run_test()
        except: 
            result = None
    logging.info(f"Throughput Test Result: {result}")
    return result


def main():
    run_throughput_test("/dev/ttyACM0", 115200)


if __name__ == "__main__": 
    logging.basicConfig(level=logging.INFO)
    main()
   