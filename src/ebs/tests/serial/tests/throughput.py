
import logging
logger = logging.getLogger("throughput")


class ThroughputTest:
    msg = b"0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    
    def __init__(self, driver, length=1000000):
        self.driver = driver
        self.length = length

    def fail(self, msg):
        logger.error(msg)
        self.driver.stop()
        result = {
            'pass': False,
            'msg': msg,
            'duration': self.driver.duration_seconds,
            'bytes_rx': self.driver.bytes_received_total,
            'bytes_tx': self.driver.bytes_transmitted_total
        }
        return result

    def succeed(self, msg=None):
        if not msg:
            msg = "Throughput Test Succeeded"
        logger.debug(msg)
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
        return result

    def start(self):
        logger.info("Commanding Throughput Test")
        self.driver.send_data(b'a')
        response = self.driver.read_data(1)
        logger.debug(f"Got response : {response}")
        
        if response != b'a':
            self.fail("Throughput application not responsive ")

    def run_test(self):
        self.start()
        while self.driver.bytes_received_total < self.length:
            data = self.driver.read_data(len(self.msg))
            # logger.debug(f"GOT {data}")
            if data != self.msg:
                return self.fail(f"Unexpected Data Recieved! Got {data}")
        return self.succeed()
        

