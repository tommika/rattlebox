import unittest
import rattlebox.nmea as nmea

class NMEATest(unittest.TestCase):
    def test_doc(self) -> None:
        self.assertIsNotNone(nmea.__doc__)

    def test_valid_message(self) -> None:
        valid = "$GPRMC,011727.000,A,4125.9840,N,07357.0713,W,0.07,159.48,140820,,,A*73"
        fields = nmea.parse_sentence(valid)
        print(fields)

    def test_invalid(self) -> None:
        self.assertRaises(Exception, lambda: nmea.parse_sentence("bogus"))
        missing_chk = "$GPRMC,011727.000,A,4125.9840,N,07357.0713,W,0.07,159.48,140820,,,A"
        self.assertRaises(Exception, lambda: nmea.parse_sentence(missing_chk))
        bad_chk = "$GPRMC,011727.000,A,4125.9840,N,07357.0713,W,0.07,159.48,140820,,,A*42"
        self.assertRaises(Exception, lambda: nmea.parse_sentence(bad_chk))

if __name__ == '__main__':
    unittest.main()