import click
import serial
import threading
import collections
from time import sleep

class SerialDriver:
    def __init__(self, url="/dev/ttyACM0", baudrate=1000000, buffer_size=1024 * 1024, timeout=1000):
        self.ser = serial.serial_for_url(
                url,
                do_not_open=True,
                baudrate=baudrate,
                timeout=timeout,
            )
        self.read_buffer = collections.deque(maxlen=buffer_size)  # 1MB read buffer
        self.write_buffer = collections.deque(maxlen=buffer_size)  # 1MB write buffer
        self.read_lock = threading.Lock()
        self.write_lock = threading.Lock()

        self._stop_threads = threading.Event()

        # Bytes transferred counters
        self.bytes_received = 0
        self.bytes_transmitted = 0
        self.bytes_received_total = 0
        self.bytes_transmitted_total = 0
        self.rate_rx_max = 0
        self.rate_tx_max = 0
        self.duration_seconds = 0

    @property
    def rate_rx_avg(self):
        return self.bytes_received_total / self.duration_seconds

    @property
    def rate_tx_avg(self):
        return self.bytes_transmitted_total / self.duration_seconds

    def __enter__(self):
        # Start reader, writer, and logger threads
        self.read_thread = threading.Thread(target=self._read_from_serial)
        self.write_thread = threading.Thread(target=self._write_to_serial)
        self.logger_thread = threading.Thread(target=self._log_transfer_rates)

        self.ser.open()
        sleep(1)
        self.ser.flush()
        self.ser.read_all()

        self.read_thread.start()
        self.write_thread.start()
        self.logger_thread.start()

        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        # Stop threads and close the serial port
        self.stop()  

    def _read_from_serial(self):
        while not self._stop_threads.is_set():
            if self.ser.in_waiting > 0:
                data = self.ser.read(self.ser.in_waiting)
                with self.read_lock:
                    self.read_buffer.extend(data)
                self.bytes_received += len(data)  # Accumulate received bytes
            # sleep(0.01)  # Slight delay to avoid excessive CPU usage

    def _write_to_serial(self):
        while not self._stop_threads.is_set():
            if self.write_buffer:
                with self.write_lock:
                    data = bytearray()
                    while self.write_buffer:
                        data.append(self.write_buffer.popleft())
                    self.ser.write(data)
                self.bytes_transmitted += len(data)  # Accumulate transmitted bytes
            sleep(0.01)

    def _log_transfer_rates(self):
        while True:
            # Log every second
            sleep(1) 
            
            self.duration_seconds += 1  
            self.bytes_received_total += self.bytes_received
            self.bytes_transmitted_total += self.bytes_transmitted
            
            received_rate = self.bytes_received
            transmitted_rate = self.bytes_transmitted 
            
            if received_rate > self.rate_rx_max:
                self.rate_rx_max = received_rate 

            if transmitted_rate > self.rate_tx_max:
                self.rate_tx_max = transmitted_rate

            click.secho(f"{self.ser.port} XFER - Rx: {(received_rate / (1024 * 1024)):0.3f} Mbytes/s, Tx: {(transmitted_rate / (1024 * 1024)):0.3f} Mbytes/s, RxT: {self.bytes_received_total}", fg="bright_black")

            # Reset counters
            self.bytes_received = 0
            self.bytes_transmitted = 0

            if self._stop_threads.is_set():
                break

    def send_data(self, data):
        """Append data to the write buffer for transmission"""
        with self.write_lock:
            self.write_buffer.extend(data)

    def read_data(self, num_bytes):
        """Read exactly num_bytes from the receive buffer"""
        while len(self.read_buffer) < num_bytes:
            sleep(0.01)
        with self.read_lock:
            data = bytearray()
            for _ in range(min(num_bytes, len(self.read_buffer))):
                data.append(self.read_buffer.popleft())
            return bytes(data)

    def stop(self):
        """Stop the reader, writer, and logger threads"""
        self._stop_threads.set()
        self.read_thread.join()
        self.write_thread.join()
        self.logger_thread.join()
        self.ser.close()
        self.flush()

    def flush(self):
        """Clear both the read and write buffers"""
        with self.read_lock, self.write_lock:
            self.read_buffer.clear()
            self.write_buffer.clear()
