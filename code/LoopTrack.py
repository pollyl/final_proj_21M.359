import sys
sys.path.append('./common')
from core import *
from audio import *
from song import *
from clock import *
from synth import *
# from metro import *


import rtmidi_python as rtmidi

from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.clock import Clock as kivyClock

from kivy.core.window import Window
from random import random

from kivy.graphics.instructions import InstructionGroup
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.graphics import PushMatrix, PopMatrix, Translate, Scale, Rotate
from kivy.clock import Clock as kivyClock

import numpy as np
import threading
import time

class LoopTrack(InstructionGroup):
    def __init__(self, top_left, size, icon_str, rgb):
      super(LoopTrack, self).__init__()
      self.top_left = top_left
      self.size = size

      # setup icon location and size
      icon_size = 80
      mid_y = top_left[1] - icon_size/2.0 - 10
      self.icon = Rectangle(source = icon_str , pos=(top_left[0], mid_y - icon_size/2.0), size=(icon_size, icon_size))

      self.color = Color(*(0, 0, 0.5), mode='hsv')
      pts = [0, self.top_left[1] - size[1], size[0], self.top_left[1] - size[1]]
      self.line = Line(points = pts, width=1)

      self.blip_color = rgb
      self.active = False

    # show the color, instrument icon, and bottom divide line
    def show(self):
        self.add(self.color)
        self.add(self.icon)
        self.add(self.line)
        print "show"

    # changes icon color to white (active)
    def set_active(self):
        self.active = True
        self.color.rgb = (1, 1, 1)

    # changes icon color to gray (inactive)
    def set_inactive(self):
        self.active = False
        self.color.rgb = (.5, .5, .5)

    # TODO Polly
    def add_blip(self, x_fraction, y_fraction):
        # calculate x-coord of the blip
        #x = float(tick)/self.loop_duration * (Window.width - 100) + 100
        x = x_fraction * (Window.width - 100) + 100
        y = -y_fraction * self.size + self.top_left[1]
        r = Rectangle(pos = (x, y, size = (20, 20))

        self.add(self.blip_color)
        self.add(r)


