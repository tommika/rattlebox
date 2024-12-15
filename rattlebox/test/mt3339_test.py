import unittest
import sys
import rattlebox.mt3339 as mt3339
import rattlebox.gpx as gpx
from typing import (Any, Optional)

class MT3339Test(unittest.TestCase):
    def test_commands(self) -> None:
        self.assertFalse(mt3339.Driver.is_valid_command("bogus"))
        for cmd in mt3339.Driver.COMMANDS:
            self.assertTrue(mt3339.Driver.is_valid_command(cmd))
        
    def test_valid_lox(self) -> None:
        words = ["03E85667","04347B25","421AE293","C235006A","12E85667","04407B25","4200E293","C2390019"]
        driver = mt3339.Driver(None,debug=True)
        points:list[gpx.Point] = driver.lox_to_points(words)
        self.assertEqual(2,len(points))
        self.assertEqual(41,int(points[0].lat))
        self.assertEqual(-73,int(points[0].lon))
        self.assertEqual(53,points[0].ele)
        print(f"points: {points}",file=sys.stderr)

    def test_invalid_lox(self) -> None:
        # wrong data length
        driver = mt3339.Driver(None,debug=True)
        words = ["03E85667","04347B25","421AE293","C235006A","12E85667","04407B25","4200E293"]
        self.assertRaises(Exception, lambda : driver.lox_to_points(words))
        # bad checksum
        words = ["03E85667","04347B25","421AE293","C235006B"]
        points:list[gpx.Point] = driver.lox_to_points(words)
        self.assertEqual(0,len(points))

    def test_messages(self) -> None:
        driver = mt3339.Driver(None,debug=True)
        driver.cmd = "logger-dump"
        with open('test-data/test-messages.txt', 'r') as file:
            messages = file.readlines()
            for msg in messages:
                self.assertTrue(driver.recv_message(msg.encode("ascii")))
        # confirm that we dumped the log
        doc = self.must_be(driver.get_log_as_gpx())
        print(doc.to_xml())
        # confirm that we tracked the current location
        loc = self.must_be(driver.get_loc())
        print(f"loc: {loc}")
        self.assertEqual(41,int(loc.lat))
        self.assertEqual(-73,int(loc.lon))
        self.assertEqual(85,loc.ele)

    def must_be(self, obj: Optional[Any]) -> Any:
        """
        Assert that the given object is not None,
        and return it.
        """
        self.assertIsNotNone(obj)
        return obj

if __name__ == '__main__':
    unittest.main()