import unittest
import time
import logging
import sys
import io
import rattlebox.gpx as gpx

class GPXTest(unittest.TestCase):
    def test_from_points(self) -> None:
        p1 = gpx.Point()
        p1.ele = 0
        p1.ts = int(time.time())
        points = [p1]
        doc = gpx.Document.from_points(points)
        gpx_str = doc.to_xml()
        print(gpx_str)

if __name__ == '__main__':
    unittest.main()