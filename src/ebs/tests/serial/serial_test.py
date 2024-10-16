
import click
from .drivers.serialport import SerialDriver
from .tests.throughput import ThroughputTest


def run_throughput_test(url, baudrate=1000000, length=1000000, timeout=10):
    click.secho(f"STARTING SERIAL THROUGHPUT TEST", bold=True)
    click.secho(f"   {url}\t{baudrate}\t{length} bytes")
    with SerialDriver(url=url, baudrate=baudrate, timeout=timeout) as link:
        test = ThroughputTest(link, length)   
        try:
            result = test.run_test()
        except: 
            result = None
    return result


def main():
    run_throughput_test("/dev/ttyACM0", 230400)


if __name__ == "__main__": 
    main()
