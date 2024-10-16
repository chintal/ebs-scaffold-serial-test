
import click
from ..drivers.serialport import SerialDriver

import logging
logger = logging.getLogger("throughput")


class ThroughputTest:
    msg = b"0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    def __init__(self, driver, length=1000000):
        self.driver = driver
        self.length = length

    def print_failure(self, result):
        click.secho(f"SERIAL THROUGHPUT TEST FAILED", bold=True, fg='red')
        click.secho(result['msg'], fg='red')
        click.secho(f"RX bytes before error:")
        click.secho(f"    {result["bytes_rx"]}")

    def print_success(self, result):
        click.secho(f"SERIAL THROUGHPUT TEST PASSED", bold=True, fg='green')
        click.secho(f"RX bytes   :     ")
        click.secho(f"    {result["bytes_rx"]} bytes", bold=True)
        click.secho(f"RX datarate:     ")
        click.secho(f"    avg : {result['rate_rx_avg']} bytes/sec", bold=True)
        click.secho(f"    max : {result['rate_rx_max']} bytes/sec")

    def fail(self, msg):
        self.driver.stop()
        result = {
            'pass': False,
            'msg': msg,
            'duration': self.driver.duration_seconds,
            'bytes_rx': self.driver.bytes_received_total,
            'bytes_tx': self.driver.bytes_transmitted_total
        }
        self.print_failure(result)
        return result

    def succeed(self, msg=None):
        if not msg:
            msg = "Throughput Test Succeeded"
        self.driver.stop()
        result = {
            'pass': True,
            'bytes_rx': self.driver.bytes_received_total,
            'bytes_tx': self.driver.bytes_transmitted_total,
            'rate_rx_max': int(self.driver.rate_rx_max),
            'rate_tx_max': int(self.driver.rate_tx_max), 
            'rate_rx_avg': int(self.driver.rate_rx_avg),
            'rate_tx_avg': int(self.driver.rate_tx_avg),
            'duration': self.driver.duration_seconds
        }
        self.print_success(result)
        return result

    def start(self):
        logger.info("Commanding Throughput Test")
        self.driver.send_data(b'a')
        response = self.driver.read_data(1)
        
        if response != b'a':
            self.fail(f"Throughput application not responsive. Got response {response}")

    def run_test(self):
        self.start()
        while self.length and self.driver.bytes_received_total < self.length:
            data = self.driver.read_data(len(self.msg))
            # logger.debug(f"GOT {data}")
            if data != self.msg:
                return self.fail(f"Unexpected Data Recieved! Got {data}")
        return self.succeed()
