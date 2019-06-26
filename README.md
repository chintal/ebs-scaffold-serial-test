
# Script for Basic Serial Communications Testing #


This script is intended for basic testing of serial links to embedded
systems over RS-232/UART/USB-CDC.

## Running the Test ##

$ python serial-test.py -h

### Baremetal Test ###

Test for actual hardware link thoughput by eliminating all possible
firmware bottlenecks.

### Throughput Test ###

Similar to the Baremetal Test, but measure effective throughput using
whatever firmware architecture exists for link management, including
whatever buffering method exists. This does not include any higher
level protocol overhead.

### PRBS Test ###

Similar to the throughput test, but uses a PRBS instead of a simply
incrementing byte value. While this is theoretically a 'better' test,
in reality it likely does not make much difference for regular UART
links. The actual generation of the PRBS, however, does take finite
time and has been found to be a limiting step on the firmware side,
making it unsuitable for testing throughput capability.

### Protocol Tests ###

(NOT YET IMPLEMENTED)

Test for throughput including higher level protocol overhead. This is
not currently implemented.


## Dependencies ##

### PRBS (ebs-lib-prbs) ###

This script requires a simple C PRBS library to generate pseudo random
bitstreams. This same library in a form compatible with `cmake` and for
static linkage with embedded code can be found on
[github](https://github.com/chintal/ebs-lib-prbs).

## Firmware Preparation ##

TBD
