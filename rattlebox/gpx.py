# Copyright (c) 2024 Thomas Mikalsen. Subject to the MIT License
# vim: ts=4 sw=4 
"""
GPX data model and serialization to XML
"""

from typing import (Any,Self)
from collections.abc import Mapping
from dataclasses import (dataclass, field)
import io
from xml.dom.minidom import parseString as parse_xml
from xml.sax.saxutils import XMLGenerator
from xml.sax.xmlreader import AttributesNSImpl
from datetime import (datetime,timezone)

GPX_NS = "http://www.topografix.com/GPX/1/1"
NO_ATTRS = AttributesNSImpl({}, {})

@dataclass
class Point:
    """
    A point on the surface of the earth recorded by a GPS receiver
    """
    ts: int = 0 # Unix/epoch
    lat: float = 0 # decimal degrees
    lon: float = 0 # decimal degrees
    ele: int = 0 # meters

    def is_valid(self) -> bool:
        if self.ts < 978325200 or self.ts > 4102462800: # [2001-01-01 ... 2100-01-01]
            return False
        # TODO sanity check on lat/lon
        return True

    def to_xml(self, xml:XMLGenerator):
        attr_names = map({ ("", u'lat'): u'lat', ("", u'lon'): u'lon', })
        attr_vals = map({ ("", u'lat'): str(self.lat), ("", u'lon'): str(self.lon), })
        attrs = AttributesNSImpl(attr_vals, attr_names)
        xml.startElementNS(("", u'trkpt'), u'trkpt', attrs)
        xml.startElementNS(("", u'time'), u'time', NO_ATTRS)
        xml.characters(datetime.fromtimestamp(self.ts,tz=timezone.utc).isoformat())
        xml.endElementNS(("", u'time'), u'time')
        xml.startElementNS(("", u'ele'), u'ele', NO_ATTRS)
        xml.characters(str(self.ele))
        xml.endElementNS(("", u'ele'), u'ele')
        xml.endElementNS(("", u'trkpt'), u'trkpt')

@dataclass
class Segment:
    """
    A segment of a GPS track
    """
    points: list[Point] = field(default_factory=list)
    def len(self) -> int:
        return len(self.points)
    def add_point(self, pt:Point) -> None:
        self.points.append(pt)
    def add_points(self, pts:list[Point]) -> None:
        for pt in pts:
            self.points.append(pt)
    def to_xml(self, xml:XMLGenerator) -> None:
        xml.startElementNS(("", u'trkseg'), u'trk', NO_ATTRS)
        for pt in self.points:
            pt.to_xml(xml)
        xml.endElementNS(("", u'trkseg'), u'trk')

@dataclass
class Track:
    """
    A GPS track
    """
    segs: list[Segment] = field(default_factory=list)
    def add_seg(self, seg:Segment) -> None:
        self.segs.append(seg)
    def to_xml(self, xml:XMLGenerator) -> None:
        xml.startElementNS(("", u'trk'), u'trk', NO_ATTRS)
        for seg in self.segs:
            seg.to_xml(xml)
        xml.endElementNS(("", u'trk'), u'trk')

@dataclass
class Document:
    """
    A GPX Document
    """
    tracks: list[Track] = field(default_factory=list)

    def add_track(self, track:Track) -> None:
        self.tracks.append(track)

    def to_xml(self, pretty:bool = True) -> str:
        out = io.StringIO()
        xml = XMLGenerator(out, 'utf-8', True)
        root_attr_names = map({ 
            ("", u'xmlns'): u'xmlns', 
            ("",u'version'): u'version',
            ("",u'creator'): u'creator',
        })
        root_attr_vals = map({ 
            ("", u'xmlns'): GPX_NS, 
            ("",u'version'): u'1.1',
            ("",u'creator'): u'rattlebox',
        })
        root_attrs = AttributesNSImpl(root_attr_vals, root_attr_names)
        xml.startElementNS(("", u'gpx'), u'gpx', root_attrs)
        for track in self.tracks:
            track.to_xml(xml)
        xml.endElementNS(("", u'gpx'), u'gpx')
        xml.endDocument()
        gpx_str = out.getvalue()
        if pretty:
            dom = parse_xml(gpx_str)
            gpx_str = dom.toprettyxml(indent="  ")
        return gpx_str

    @classmethod
    def from_points(cls,points:list[Point]) -> Self:
        seg = Segment()
        seg.add_points(points)
        track = Track()
        track.add_seg(seg)
        doc = cls()
        doc.add_track(track)
        return doc

def map(m:Mapping) -> Mapping:
    """
    Make mypy happy.
    """
    return m
