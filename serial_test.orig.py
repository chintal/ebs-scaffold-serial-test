# Copyright (c)
# (c) 2015-16 Chintalagiri Shashank, Quazar Technologies Pvt. Ltd.
#
# This file is part of serial-test.
#
# serial-test is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# serial-test is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with serial-test.  If not, see <http://www.gnu.org/licenses/>.

"""
Simple serial communications testing script
"""

from __future__ import print_function
import argparse
import serial
import threading
import time
import datetime
import atexit
try:
    from ebs import prbs
except ImportError:
    prbs = None
import os
import sys

try:
    import pytest
except ImportError:
    pytest = None

# LIBMODBUS_FOLDER = "../../../components/libmodbus/"

lprbs = None
recieved_bytes = 0
error_bytes = 0
total_recieved_bytes = 0
total_error_bytes = 0
throughput = 0


def dump_status():
    global throughput
    global next_dump
    global total_recieved_bytes
    global total_error_bytes

    if total_recieved_bytes > 0:
        byer = 1.00 * total_error_bytes / total_recieved_bytes
    else:
        byer = 0.00
 
    print('{0}::{1} bytes/sec :: BYER :{2} :: Total :{3} :: Errors :{4}' \
          ''.format(datetime.datetime.now(), throughput, byer,
                    total_recieved_bytes, total_error_bytes)
          )


def update_status():
    global recieved_bytes
    global error_bytes
    global total_error_bytes
    global total_recieved_bytes
    global throughput
    global next_update

    throughput = recieved_bytes

    total_recieved_bytes += recieved_bytes
    recieved_bytes = 0

    total_error_bytes += error_bytes
    error_bytes = 0

    dump_status()

    next_update += 1
    threading.Timer(next_update - time.time(), update_status).start()


def init_prbs():
    global lprbs
    lprbs = prbs.lfsr16_t()
    prbs.lfsr_vInit(lprbs, int(prbs.LFSR_DEFAULT_SEED), int(prbs.LFSR_DEFAULT_TAPS))
    return


def begin_prbs_test(layer2):
    global recieved_bytes
    global error_bytes
    global lprbs
    if prbs is None:
        print("PRBS library not found. Cannot perform PRBS test.")
        return
    init_prbs()
    layer2.write('b'.encode())
    expected_char = prbs.lfsr_cGetNextByte(lprbs)
    sync = 0
    print("Waiting for Sync")
    while not sync:
        char = layer2.read().decode('ascii')
        if char == 'b':
            sync = 1
            print("Synced")
    global next_update
    next_update = time.time()
    update_status()
    while 1:
        char = layer2.read()
        if str(format(ord(char), '02x')) != str(format(expected_char, '02x')):
            print("Received: {0} :: Expected : {1}"
                  "".format(ord(char), expected_char))
            error_bytes += 1
        recieved_bytes += 1
        expected_char = prbs.lfsr_cGetNextByte(lprbs)
        if error_bytes > 25:
            break


def begin_throughput_test(layer2, cmd):
    global recieved_bytes
    global error_bytes
    print("Sending command")
    layer2.write(cmd.encode())
    expected_char = ord('0')
    sync = 0
    print("Waiting for Sync")
    while not sync:
        char = layer2.read().decode('ascii')
        print("Got: {0}, Want: {1}, {2}".format(char, cmd, char == cmd))
        if char == cmd:
            sync = 1
            print("Synced")
    global next_update
    next_update = time.time()
    update_status()
    while 1:
        char = layer2.read()
        if ord(char) != expected_char:
            print("R:{0} E:{1} Nb: {2:>4} Ne:{3:>4}" \
                  "".format(char, chr(expected_char),
                            recieved_bytes, error_bytes))
            error_bytes += 1
        recieved_bytes += 1
        if expected_char is ord('Z'):
            expected_char = ord('0')
        else:
            expected_char += 1
        if error_bytes > 50:
            break


# http://www.englishinuse.net/
test_strings = [
    'The cat is in the well.##',
    'Do you spend much time writing email?###',
    "I'm hungry, so I'm going to get something to eat.#",
    'She screamed for help.###',
    'She agreed with him on what to do with the old car.####',
    'Is it possible?',
    'Tom saw something red there.##'
    'She dumped him.',
    'I have some English books.####',
    'The more I think about it, the less I understand it.###',
    'I was in the mountains.##',
    'She accompanied him to Japan.#',
    "Isn't it black?",
    'I could swim well even when I was a child.###',
    "It's fun to play baseball.####",
    'I know you can make it.##',
    'Do you know where she went?###',
    "I think it's time for me to organize a party.",
    'Did you watch the game last night?#',
    'Why do you ask?',
    'There are many people here.###',
    'He bowed to me as he left the room.',
    "I think it's time for me to abandon that idea.####",
    'She is two years older than you.###',
    'I am not concerned with this.#',
    'I changed my mind.##',
    'Does this book belong to you?#',
    "Let's take a break for coffee.",
    'He ran away with the money.###',
    "She's my classmate.#"
]


def _roundtrip_sender(layer2):
    sidx = 0
    while True:
        # print("Sending :: {0}".format(test_strings[sidx].encode()))
        layer2.write(test_strings[sidx].encode())
        sidx += 1
        if sidx == len(test_strings):
            sidx = 0


def begin_roundtrip_test(layer2, cmd):
    global recieved_bytes
    global error_bytes
    layer2.write(cmd.encode())
    sync = 0
    print("Waiting for Sync")
    while not sync:
        char = layer2.read().decode('ascii')
        # print("Got {0}".format(char))
        if char == cmd:
            sync = 1
            print("Synced")
    global next_update
    next_update = time.time()
    update_status()
    sending_thread = threading.Thread(target=_roundtrip_sender, args=(layer2,), daemon=True)
    sending_thread.start()
    sidx = 0
    while 1:
        rstr = layer2.read(len(test_strings[sidx])).decode()
        # print("Got     :: {0}".format(rstr))
        if rstr != test_strings[sidx]:
            print("ERROR :: {0} : {1}".format(rstr, test_strings[sidx]))
            error_bytes += len(rstr)
            break
        recieved_bytes += len(rstr)
        sidx += 1
        if sidx == len(test_strings):
            sidx = 0


# def begin_modbus_test(port, baud, slaveaddress):
#     # layer2.write(chr(0x05))
#     # layer2.write(chr(0x06))
#     # layer2.write(chr(0x00))
#     # layer2.write(chr(0x04))
#     # layer2.write(chr(0x01))
#     # layer2.write(chr(0x01))
#     # layer2.write(chr(0x09))
#     # layer2.write(chr(0xDF))
#     if pytest is None:
#         print ('py.test is not installed. Cannot run modbus test.')
#     os.chdir(os.path.join(LIBMODBUS_FOLDER, 'scaffold', 'tests', 'software'))
#     port = os.path.relpath(port, '/dev')
#     pytest.main(['-v', '--baud', baud, '--saddr', slaveaddress, '--port', port])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', default='/dev/ttyACM0',
                        help="Serial Port",)
    parser.add_argument('-b', '--baudrate', default=256000, type=int,
                        help="Baud Rate. Not applicable to USB CDC links")
    parser.add_argument('test', choices=['baremetal', 'throughput',
                                         'prbs', 'roundtrip', 'chunkedtrip',
                                         'modbus'],
                        default='prbs', help='Type of test to run')
    args = parser.parse_args()
    # if args.test == 'modbus':
    #     begin_modbus_test(args.port, args.baudrate, 5)
    #     sys.exit(0)
    ser = serial.Serial(args.port, baudrate=args.baudrate, timeout=1)
    atexit.register(ser.close)
    ser.flushInput()
    ser.flushOutput()
    ser.timeout = 1
    i = 0
    drain = ser.read()
    while len(drain) == 1:
        drain = ser.read()
        i += 1
    print("Drained {0} bytes".format(i))
    ser.timeout = 1
    if args.test == 'prbs':
        begin_prbs_test(ser)
    elif args.test == 'throughput':
        begin_throughput_test(ser, 'a')
    elif args.test == 'baremetal':
        begin_throughput_test(ser, 'c')
    elif args.test == 'roundtrip':
        begin_roundtrip_test(ser, 'd')
    elif args.test == 'chunkedtrip':
        begin_roundtrip_test(ser, 'e')
    else:
        print("{0} test is not implemented".format(args.test))
