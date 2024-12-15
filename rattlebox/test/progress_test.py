import unittest
import rattlebox.progress as progress
import sys

class ProgressTest(unittest.TestCase):
    def test_progress(self) -> None:
        prog = progress.Progress(max=4,label="Wow: ",width=8)
        max = 100
        progRock = progress.Progress(max=max,label="Close to the Edge: ",width=32)
        for _ in range(50):
            progRock.display(sys.stdout,delta=1)
        self.assertEqual(50,progRock.get())
        for _ in range(100):
            progRock.display(sys.stdout,delta=1)
        self.assertEqual(100,progRock.get())
        self.assertEqual(0,prog.get())
