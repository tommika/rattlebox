# Copyright (c) 2024 Thomas Mikalsen. Subject to the MIT License
# vim: ts=4 sw=4 
from typing import (TextIO)
import math
import shutil

class Progress:
    """
    Simple progress bar
    """
    def __init__(self,max:int,cur:int=0,bar=True,fract=True,fill='',blank='',label:str="",width:int=-1):
        if bar and width==-1:
            # set width based on terminal width
            try:
                width, _ = shutil.get_terminal_size()
                width -= len(label)
                width -= 2 # border around bar
                if fract:
                    # fraction: " (max/max)"
                    n = int(1+math.log10(max)) if max>0 else 1
                    width -= (2*n + 4)
            except:
                # what else is there to do?
                width = 10
            width = min(max,width)
        self.label = label
        self.width = width
        self.max = max
        self.set(cur)
        self.fract = fract
        self.bar = bar
        self.fill = fill[0] if len(fill)>0 else '#'
        self.blank = blank[0] if len(blank)>0 else ' '
    def set(self,cur:int):
        self.cur = max(0,min(cur,self.max))
    def get(self) -> int:
        return self.cur
    def inc(self,delta:int=1):
        self.set(self.cur + delta)
    def display(self,out:TextIO,delta:int=0):
        self.inc(delta)
        out.write(f"\r{self.label}")
        if self.bar:
            out.write(f"[{self.__bar()}]")
        if self.fract:
            out.write(f" ({self.cur}/{self.max})")
        out.flush()
    def __bar(self) -> str:
        # construct the progress bar
        p = (self.cur * self.width) // self.max
        c = lambda i : self.fill if i<p else self.blank
        return "".join([ c(i) for i in range(self.width) ])



