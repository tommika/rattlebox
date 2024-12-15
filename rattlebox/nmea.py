# Copyright (c) 2024 Thomas Mikalsen. Subject to the MIT License
# vim: ts=4 sw=4 
"""
The nmea module provides functions for working with NMEA 0183 messages.
See:
* https://en.wikipedia.org/wiki/NMEA_0183
* https://aprs.gids.nl/nmea/
"""

from typing import (Optional)
import rattlebox.gpx as gpx
from datetime import datetime, timezone

def parse_sentence(line:str) -> list[str]:
    """
    Parse and validate an NMEA sentence.
    Returns the fields as a list of strings
    """
    if line[0] != "$":
        raise Exception("invalid sentence: missing start delimiter")
    body_chk = line.split('*')
    if len(body_chk) != 2 or len(body_chk[1]) != 2:
        raise Exception(f"invalid sentence: missing or invalid checksum")
    # verify checksum
    chk = checksum(body_chk[0][1:])
    if chk != body_chk[1]:
        raise Exception(f"invalid sentence: checksum does not match: expected {body_chk[1]}; computed {chk}")
    fields = body_chk[0].split(",")
    return fields

def checksum(body:str):
    """
    Compute the checksum of the body of a NMEA sentence
    """
    chk = 0
    for c in body:
        chk = chk ^ ord(c)
    return '%02X' % (chk)

def parse_gpgga(fields:list[str]) -> Optional[gpx.Point]:
    """
    Parse Global Positioning System Fix Data
    """
    if len(fields)<15 or fields[6]==0:
        # invalid data
        return None
    pt = gpx.Point()
    pt.lat = parse_deg(fields[2])
    if fields[3] == 'S':
        pt.lat *= -1
    pt.lon = parse_deg(fields[4])
    if fields[5] == 'W':
        pt.lon *= -1
    if fields[10] == 'M':
        pt.ele = int(float(fields[9]))

    # REVIEW: how to get this from the device? the GGA packet contains UTC time but not date.
    pt.ts = int(datetime.now(timezone.utc).timestamp())

    return pt

def parse_deg(val:str) -> float:
    """
    Input format is: [...]DMM.M[...]
    Output is decimal degrees.
    E.g.,
      input: 4125.3610 = 41 deg, 25.361 mins
      output: 41.42268333... deg
    """
    dot = val.find('.')
    if dot<3:
        return float('nan')
    mins = float(val[dot-2:])
    deg = int(val[:dot-2])
    return deg + mins/60
