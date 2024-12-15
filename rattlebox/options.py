# Copyright (c) 2024 Thomas Mikalsen. Subject to the MIT License
# vim: ts=4 sw=4 

from typing import (Optional, Self, TextIO)
from dataclasses import (dataclass, field)
import sys
import rattlebox.mt3339 as mt3339

@dataclass
class Options:
    """
    GPS driver options
    """
    DEF_BAUD = 115200 
    help:bool = False
    device:str = "" # device name; e.g., "/dev/tty.usbserial-410"
    baudrate:int = DEF_BAUD # serial port baud rate; e.g., 115200
    timeout:int = 2 # serial port timeout
    debug:bool = False
    show_prog:bool = True
    follow:bool = False
    logfile:Optional[str] = None
    commands:list[str] = field(default_factory=list) # list of commands to send to device

    @staticmethod
    def usage(progname:str, out:TextIO=sys.stderr) -> None:
        print(f"Usage: {progname} <device> [<option> ...] [<command> ...]", file=out)
        print(f" where <command> is one of:", file=out)
        for c in sorted(mt3339.Driver.COMMANDS):
            cmd = mt3339.Driver.COMMANDS[c]
            print(f"\t{c}", end='', file=out)
            if cmd.help is not None:
                print(f" : {cmd.help}", end='', file=out)
            print(file=out)
        print(" and <option> is one of:", file=out)
        print(f"\t--b|baud <baud-rate> : defaults to {Options.DEF_BAUD}", file=out)
        print(f"\t--l|log <log-file> : save log data (as GPX) to the given file", file=out)
        print(f"\t--d|debug", file=out)
        print(f"\t--f|follow : echo output from device", file=out)
        print(f"\t--?|help", file=out)
        print(f"\t--no-progress : don't show progress", file=out)
        print(f"e.g.,", file=out)
        print(f"{progname} /dev/ttyUSB0 --baud 9600 logger-status", file=out)
        print(f"{progname} COM6 9600 logger-status", file=out)

    @classmethod
    def from_args(cls,args_orig:list[str]) -> Self:
        args:list[str] = []
        for a in args_orig:
            if a.startswith('-'):
                # convert "-n=b" to ["-n","b"]
                for s in a.split("=",1):
                    args.append(s)
            else:
                args.append(a)
        cfg = cls()
        iarg = 0
        def require_arg() -> int:
            if iarg+1>=len(args):
                raise Exception(f"required argument missing: {arg} ...")
            return iarg + 1
        while iarg<len(args):
            arg = args[iarg]
            if arg.startswith('-'):
                arg = arg.lstrip('-')
                if arg in ["?","help"]:
                    cfg.help = True
                elif arg in ["d","debug"]:
                    cfg.debug = True
                elif arg in ["no-progress"]:
                    cfg.show_prog = False
                elif arg in ["f","follow"]:
                    cfg.follow = True
                elif arg in ["b","baud"]:
                    iarg = require_arg()
                    rate = args[iarg]
                    cfg.baudrate = parse_int(rate,0)
                    if cfg.baudrate < 9600:
                        raise Exception(f"Invalid baud rate: {rate}")
                elif arg in ["l","log"]:
                    iarg = require_arg()
                    cfg.logfile = args[iarg]
                else:
                    raise Exception(f"Unrecognized option: {arg}")
            elif len(cfg.device) == 0:
                cfg.device = arg
            elif arg in mt3339.Driver.COMMANDS:
                cfg.commands.append(arg)
            else:
                raise Exception(f"Unrecognized argument: {arg}")
            iarg += 1
        if not cfg.help and len(cfg.device) == 0:
            raise Exception("Required arguments missing")
        return cfg


def parse_int(arg:str, default:int) -> int:
    """
    Parse an integer argument.  Returns default if not a valid int.
    """
    val = default
    if len(arg)>0:
        try:
            val=int(arg)
        except ValueError as e:
            pass
    return val