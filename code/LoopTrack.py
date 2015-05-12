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

from kivyparticle import ParticleSystem
from kivy.properties import NumericProperty, BooleanProperty, ListProperty, StringProperty, ObjectProperty

import numpy as np
import threading
import time

#KeyFrame Animation

class KFAnim(object):
   def __init__(self, xs, ys):
      super(KFAnim, self).__init__()
      self.xs = xs
      self.ys = ys

   def eval(self, t):
      return np.interp(t, self.xs, self.ys)


class Bubble(InstructionGroup):
   def __init__(self, pos, r, color, duration = 3):
      super(Bubble, self).__init__()

      self.pos = pos
      self.duration = duration
      self.radius_anim = KFAnim((0, .1, self.duration), (r, 2*r, 0))
      self.x_anim = KFAnim((0, self.duration), (pos[0], 400))
      self.y_anim = KFAnim((0, self.duration), (pos[1], 300))

      self.color = Color(*color, mode="hsv")
      self.circle = Ellipse(segments = 40)

      self.add(self.color)
      self.add(self.circle)

      self.time = 0
      self.on_update(0)

      self.isActive = False

   def _set_pos(self, pos, radius):
      self.circle.pos = pos[0] - radius, pos[1] - radius
      self.circle.size = radius * 2, radius * 2

   def on_update(self, dt):
      self.time += dt

      # rad = self.radius_anim.eval(self.time)
      # self._set_pos(self.pos, rad)

      pos = (self.x_anim.eval(self.time), self.y_anim.eval(self.time))
      rad = self.radius_anim.eval(self.time)
      self._set_pos(pos, rad)

      # continue flag
      return self.time < 3.0

   def update_active_status(self, isActive):
      self.isActive = isActive
      if self.isActive:
        self.color.a = 0.0
      else:
        self.color.a = 1.0



class LoopTrack(InstructionGroup):
    def __init__(self, top_left, size, icon_str, hsv):
      super(LoopTrack, self).__init__()
      self.top_left = top_left
      self.size = size

      # setup icon location, size, color
      self.icon_size = 100
      mid_y = top_left[1] - self.icon_size/2.0 - 25
      self.icon = Rectangle(source = icon_str , pos=(top_left[0], mid_y - self.icon_size/2.0), size=(self.icon_size, self.icon_size))
      self.color = Color(*(0, 0, 0.5), mode='hsv')

      # horizontal divide line
      pts = [0, self.top_left[1] - size[1], size[0], self.top_left[1] - size[1]]
      self.line = Line(points = pts, width=1)

      self.blip_color = hsv
      self.active = False
      self.blip_dic = {}

      # setup particles
      c = Color(*hsv, mode='hsv')
      self.sun = ParticleSystem('media/fireworks2.pex')
      self.sun.start_color = [c.r, c.g, c.b, 1.]
      self.sun.start_color_variance = [.2, .2, .2, 0]
      self.sun.end_color = [c.r, c.g, c.b, 1.]
      self.sun.end_color_variance = [.2, .2, .2, 0]


    # show the color, instrument icon, and bottom divide line
    def show(self):
        self.add(self.color)
        self.add(self.icon)
        self.add(self.line)

        # particles
        self.show_particles(self.sun, (300, 300))
        #print Window.children


    def hide_particles(self):
       print "hiding"
       Window.remove_widget(self.sun)
       #self.sun.stop(True)

    def show_particles(self, particles, pos):
       particles.emitter_x = pos[0]
       particles.emitter_y = pos[1]
       Window.add_widget(self.sun)
       particles.start()

    # changes icon color to white (active)
    def set_active(self):
        self.active = True
        self.color.hsv = (0, 0, 1)

    # changes icon color to gray (inactive)
    def set_inactive(self):
        self.active = False
        self.color.hsv = (0, 0, 0.5)

    def add_blip(self, x_fraction, y_fraction, note):
        # calculate x-coord of the blip
        #x = float(tick)/self.loop_duration * (Window.width - 100) + 100
        x = x_fraction * (Window.width - 100) + 105
        #y = -y_fraction * self.size[0] + self.top_left[1]

        note_height = int(((note-35)/51.0) * 0.9 * self.size[1])
        y = self.top_left[1] - self.size[1] + note_height + 6

        bubble = Bubble((x, y), 3, self.blip_color)
        self.add(bubble)
        self.blip_dic[x_fraction] = bubble

        """p = ParticleSystem('media/fireworks2.pex')
        p.max_num_particles = 25
        self.show_particles(p, (x, y))
        self.particle_dic[x_fraction] = p"""


    def clear(self):
       for key in self.blip_dic:
         bubble = self.blip_dic[key]
         self.remove(bubble)
       self.blip_dic = {}
       # super janky way of hiding emitter after clearing
       self.sun.emitter_x = -100
       self.sun.emitter_y = -100

    # check if the now bar is touching any of the loop's blips
    # If it is, animate the blip
    def on_update(self, x_frac):
      for target_frac in self.blip_dic.keys():
        #print "keys"
        #print self.blip_dic.keys()
        #print self.particle_dic.keys()
        bubble = self.blip_dic[target_frac]

        if x_frac < target_frac + 0.08 and x_frac > target_frac - 0.02:
          bubble.update_active_status(True)
          #particles.start()
          #self.show_particles(self.sun, (bubble.pos[0], bubble.pos[1]))
          self.sun.emitter_x = bubble.pos[0]
          self.sun.emitter_y = bubble.pos[1]

        else:
          bubble.update_active_status(False)
          #self.hide_particles()





