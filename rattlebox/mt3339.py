# Copyright (c) 2024 Thomas Mikalsen. Subject to the MIT License
# vim: ts=4 sw=4 
from typing import (Any, Optional)
import rattlebox.gpx as gpx
import rattlebox.nmea as nmea
import rattlebox.progress as progress
from dataclasses import dataclass
import struct
import sys

@dataclass
class Command:
    body:str # message sent to device
    help:Optional[str] = None # human readable help string
class Driver:
    """
    MT3339 driver
    """
    # commands that we can send to the device
    COMMANDS:dict[str,Command] = {
        'output-all'       : Command('PMTK314,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0',"turn on all output"),
        'output-off'       : Command('PMTK314,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0',"turn off all output"),
        'output-grmc-only' : Command('PMTK314,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0',"GRMC output only"),
        'logger-status'    : Command('PMTK183',"get logger status"),
        'logger-erase'     : Command('PMTK184,1',"erase logger firmware"),
        'logger-start'     : Command('PMTK185,0',"start logging"),
        'logger-stop'      : Command('PMTK185,1',"stop logging"),
        #'logger-now'       : Command('PMTK186,1',"no idea"),
        'logger-dump'      : Command('PMTK622,1',"export logger data"),
        #'logger-config'    : Command('PMTK187,1',"configure logger"),
        'baud-9600'        : Command('PMTK251,9600',"set device baud rate to 9600"),
        'baud-115200'      : Command('PMTK251,115200',"set device baud rate to 115200"),
        }

    def __init__(self,port:Any, debug:bool = False, show_prog:bool = True):
        self.port = port
        self.debug = debug
        self.show_prog = show_prog
        self.cmd:Optional[str] = None # the currently active command (if any)
        self.log_points:list[gpx.Point] = [] # points from latest logger dump
        self.prog:Optional[progress.Progress] = None
        self.loc:Optional[gpx.Point] = None

    def get_log_as_gpx(self) -> Optional[gpx.Document]:
        return gpx.Document.from_points(self.log_points) if len(self.log_points)>0 else None
    
    def get_loc(self) -> Optional[gpx.Point]:
        return self.loc

    def send_command(self, cmd:str):
        if not cmd in self.COMMANDS:
            raise Exception(f"unrecognized command: {cmd}")
        # Send command message to device
        body = type(self).COMMANDS[cmd].body
        # build message for the command
        msg = '$%s*%s\r\n' % (body, nmea.checksum(body))
        msg_bytes = msg.encode("ascii")
        if self.debug:
            print(f"[send] {msg_bytes!r}", file=sys.stderr)
        self.port.write(msg_bytes)
        self.cmd = cmd

    def is_command_active(self) -> bool:
        """
        Determines if there is a currently activate command.
        """
        return self.cmd is not None

    def recv_message(self, msg_bytes:bytes) -> bool:
        """
        Receive a message from the device.
        """
        if self.debug:
            print(f"[recv] {msg_bytes!r}", file=sys.stderr)
        msg:str = ""
        fields:list[str] = []
        try:
            msg = msg_bytes.decode("ascii").rstrip()
            if len(msg)>0:
                fields = nmea.parse_sentence(msg)
        except Exception as e:
            if self.debug:
               print(f"error reading from device: {e}",file=sys.stderr)
        if len(fields)==0:
            return False
        if fields[0].startswith("$PMTK"):
            self.handle_pmtk(fields)
        elif fields[0].startswith("$GP"):
            self.handle_nmea(fields)
        else:
            # unrecognized packet
            if self.debug:
               print(f"unrecognized packet identifier: {fields[0]}",file=sys.stderr)
            return False
        return True

    def handle_pmtk(self,fields:list[str]):
        """
        Handle a MTK-specific packets, typically in response to a command that
        we have sent.
        """
        if self.cmd == None:
            # unexpected packet; eat it
            if self.debug:
               print(f"unexpected packet: {fields[0]}",file=sys.stderr)
            return
        # MT packet
        match fields[0]:
            case "$PMTK001":
                # This marks the end of the response to the command that we
                # had submitted
                self.cmd = None
            case "$PMTKLOX":
                if fields[1]=='0':
                    # start of log
                    max = int(fields[2])
                    if self.show_prog:
                        self.prog = progress.Progress(max=max,label="dump log: ")
                elif fields[1]=='2':
                    # end of log
                    sys.stderr.write(f"\nlog contains {len(self.log_points)} valid points\n")
                else:
                    # Log data
                    assert(fields[1]=='1')
                    # Parse log data and add to list
                    self.log_points.extend(self.lox_to_points(fields[3:]))
                    # Show progress
                    if self.show_prog and self.prog is not None:
                        self.prog.display(sys.stderr,delta=1)
            case _:
                # any other type, just echo it for now
                print(f"{fields}",file=sys.stderr)

    def handle_nmea(self,fields:list[str]):
        """
        Handler NMEA packets
        """
        match fields[0]:
            case "$GPGGA":
                point = nmea.parse_gpgga(fields)
                if point is not None:
                    self.loc = point

    @classmethod
    def is_valid_command(cls,cmd:str) -> bool:
        return cmd in cls.COMMANDS
        
    def lox_to_points(self,lox_words:list[str]) -> list[gpx.Point]:
        """
        Convert a LOCUS/lox word list into a list of GPX points.
        According to the spec, there can be at most 24 words per LOX message.
        Each word is 32-bits (4 bytes) and encoded as a hex string.
        Words a grouped into 16 byte data blocks, with the following fields:
        * Timestamp (Unix/epoch UTC) - 4 bytes (#0-3) - unsigned long (little endian)
        * Fix type - 1 byte (#4) - byte/char
        * Latitude (decimal degrees) - 4 bytes (#5-8) - 32bit single-precision floating-point
        * Longitude (decimal degrees) - 4 bytes (#9-12) - 32bit single-precision floating-point
        * Elevation (meters) - 2 bytes (#13-14) - unsigned short (little-endian)
        * Checksum - 1 byte (#15) - xor of bytes #0-14
        """
        if len(lox_words)%4 != 0 or len(lox_words) > 24:
            # must be multiple of 4 and less than 24 words
            raise Exception("invalid LOCUS data: unexpected word count")
        # convert words to byte array
        bytes = bytearray()
        for w in lox_words:
            bytes.extend(bytearray.fromhex(w))
        # convert each 16-byte data block to a GPX point
        points:list[gpx.Point] = []
        for i in range(0,len(bytes),16):
            block = bytes[i:i+16]
            chk = checksum(block[:15])
            if chk != block[15]:
                # checksum does not match; skip this block
                if self.debug:
                    print(f"checksum does not match: expected {block[15]}; computed {chk}")
                continue
            wp = gpx.Point()
            wp.ts = int.from_bytes(block[0:4],"little")
            fix = bytes[4]
            wp.lat = struct.unpack('f', block[5:9])[0]
            wp.lon = struct.unpack('f', block[9:13])[0]
            wp.ele = int.from_bytes(block[13:15],"little")
            if (fix==2 or fix==4) and wp.is_valid():
                points.append(wp)
        return points

def checksum(bytes:bytearray) -> int:
    """
    Compute the checksum of the given byte array
    """
    chk = 0
    for b in bytes:
        chk = chk ^ b
    return chk

