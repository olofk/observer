import serial
import sys
import umsgpack

dev = sys.argv[1] if len(sys.argv) > 1 else '/dev/ttyUSB0'

with serial.Serial(dev, 57600) as ser:
    while(True):
        print(umsgpack.unpack(ser))
