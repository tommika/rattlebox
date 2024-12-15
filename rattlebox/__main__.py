# Copyright (c) 2024 Thomas Mikalsen. Subject to the MIT License
# vim: ts=4 sw=4 
from typing import (Optional)
from serial import Serial
import sys
import traceback

import rattlebox.gpx as gpx
import rattlebox.nmea as nmea
import rattlebox.mt3339 as mt3339
import rattlebox.options as options

RATTLEBOX = "rattlebox"

try:
    opts = options.Options.from_args(sys.argv[1:])
except Exception as e:
    print(e,file=sys.stderr)
    options.Options.usage(RATTLEBOX,sys.stderr)
    sys.exit(1)

if opts.help:
    options.Options.usage(RATTLEBOX,sys.stdout)
    sys.exit(0)


if opts.debug:
    print(f"[options] {opts}", sys.stderr)

try:
    port = Serial(opts.device, opts.baudrate, timeout=opts.timeout)
    if (port.is_open == False):
        port.open()
    port.flush()
except Exception as e:
    print(f"failed to open serial device: {type(e)} {e}")
    sys.exit(2)

try:
    driver = mt3339.Driver(port,debug=opts.debug,show_prog=opts.show_prog)
    for cmd in opts.commands:
        driver.send_command(cmd)
        if cmd.startswith("baud-"):
            # Will not get a reasonable response when changing baud
            # TODO: reopen serial port using new baud rate
            pass
        else:
            # process command response packets
            while driver.is_command_active():
                driver.recv_message(port.readline())
    # write the log as GPX, if there is one
    doc = driver.get_log_as_gpx()
    if doc is not None:
        gpx_str = doc.to_xml()
        if opts.logfile is None:
            sys.stdout.write(gpx_str)
        else:
            print(f"writing log to GPX file {opts.logfile}", file=sys.stderr)
            with open(opts.logfile, 'w') as out:
                out.write(gpx_str)
    # if follow is enabled, continue processing messages from the device
    while opts.follow:
        driver.recv_message(port.readline())
        loc = driver.get_loc()
        if loc is not None:
            print(f"\r{loc}    ",file=sys.stderr)
except KeyboardInterrupt as e:
    pass
except Exception as e:
    print(f"unexpected exception caught: {type(e)} {e}",file=sys.stderr)
    if opts.debug:
        print(traceback.format_exc())
    sys.exit(3)
finally:
    port.close()

