#! /usr/bin/env python3

import serial, time
import subprocess
from subprocess import call, Popen
from argparse import ArgumentParser
import re
import sys
import datetime
import serial.tools.list_ports as list_ports
import tempfile

COLOR_RED    = "\x1b[31m"
COLOR_GREEN  = "\x1b[32m"
COLOR_YELLOW = "\x1b[33m"
COLOR_WHITE  = "\x1b[37m"
COLOR_RESET  = "\x1b[0m"

def print_line(line):
    if "WARNING" in line:
        line = line.replace("WARNING", f"{COLOR_YELLOW}WARNING{COLOR_RESET}", 1)
    elif "WARN" in line:
        line = line.replace("WARN", f"{COLOR_YELLOW}WARN{COLOR_RESET}", 1)
    elif "ERROR" in line:
        line = line.replace("ERROR", f"{COLOR_RED}ERROR{COLOR_RESET}", 1)
    elif "INFO" in line:
        line = line.replace("INFO", f"{COLOR_WHITE}INFO{COLOR_RESET}", 1)

    if "PASSED" in line:
        line = line.replace("PASSED", f"{COLOR_GREEN}PASSED{COLOR_RESET}", 1)

    if "FAILED" in line:
        line = line.replace("FAILED", f"{COLOR_RED}FAILED{COLOR_RESET}", 1)

    if "\n" in line:
        current_time = datetime.datetime.now()
        print('[{0}] {1}'.format(current_time.isoformat(timespec='milliseconds'), line), end='')
    else:
        print('{0}'.format(line), end='')


def monitor_firmware_upload(port_url, baudrate):
    ser = serial.serial_for_url(url=port_url, baudrate=baudrate, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=3, xonxoff=False, rtscts=False, dsrdtr=False, inter_byte_timeout=1)

    timeout = 180  # 3 minutes
    timeout_start = time.monotonic()
    timeout_newline = time.monotonic()

    return_code = 0

    while True:
        serial_line = ser.readline().decode("ascii", errors='ignore')

        if len(serial_line) > 0:
            if "ERROR" in serial_line:
                return_code = -1

            print_line(serial_line)

            if "NuttShell (NSH)" in serial_line:
                sys.exit(return_code)
            elif "nsh>" in serial_line:
                sys.exit(return_code)

        else:
            if time.monotonic() > timeout_start + timeout:
                print("Error, timeout")
                sys.exit(-1)

            # newline every 10 seconds if still running
            if (len(serial_line) <= 0) and (time.monotonic() - timeout_newline > 10):
                timeout_newline = time.monotonic()
                ser.write("\n".encode("ascii"))


def main():

    default_device = None
    device_required = True

    # select USB UART as default if there's only 1
    ports = list(serial.tools.list_ports.grep('USB UART'))

    if (len(ports) == 1):
        default_device = ports[0].device
        device_required = False

        print("Default USB UART port: {0}".format(ports[0].name))
        print(" device: {0}".format(ports[0].device))
        print(" description: \"{0}\" ".format(ports[0].description))
        print(" hwid: {0}".format(ports[0].hwid))
        #print(" vid: {0}, pid: {1}".format(ports[0].vid, ports[0].pid))
        #print(" serial_number: {0}".format(ports[0].serial_number))
        #print(" location: {0}".format(ports[0].location))
        print(" manufacturer: {0}".format(ports[0].manufacturer))
        #print(" product: {0}".format(ports[0].product))
        #print(" interface: {0}".format(ports[0].interface))

    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--device', "-d", nargs='?', default=default_device, help='', required=device_required)
    parser.add_argument("--baudrate", "-b", dest="baudrate", type=int, help="serial port baud rate (default=57600)", default=57600)
    args = parser.parse_args()

    tmp_file = "{0}/pyserial_spy_file.txt".format(tempfile.gettempdir())
    port_url = "spy://{0}?file={1}".format(args.device, tmp_file)

    print("pyserial url: {0}".format(port_url))

    monitor_firmware_upload(port_url, args.baudrate)

if __name__ == "__main__":
   main()
