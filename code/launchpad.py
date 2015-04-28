#####################################################################
#
# launchpad.py
#
# Copyright (c) 2015, Eran Egozy
#
# Released under the MIT License (http://opensource.org/licenses/MIT)
#
#####################################################################

# common import
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
from LoopTrack import *
from LoopArpeg import *

# Class that contains instructions for UI graphics components (record button, instrument images, etc.)
class UIGraphics(InstructionGroup):
   def __init__(self):
      super(UIGraphics, self).__init__()
      # record button
      self.record_circle_color = Color(*(1, 1, 1), mode='hsv')
      self.record_circle = Ellipse(segments = 40, pos = (55, 20), size=(70, 70))

      # instrument select box
      self.select_box_points = [[45, 375, 135, 375, 135, 465, 45, 465, 45, 375], [45, 285, 135, 285, 135, 375, 45, 375, 45, 285], [45, 195, 135, 195, 135, 285, 45, 285, 45, 195], [45, 105, 135, 105, 135, 195, 45, 195, 45, 105]]
      self.select_box =  Line(points=self.select_box_points, width=5)

      # instruments
      self.instrument_color = Color(*(0, 0, 1), mode='hsv')
      self.instruments = [Rectangle(source="./images/guitar.png", pos=(50, 380), size=(80, 80)), Rectangle(source="./images/keyboard.png", pos=(50, 290), size=(80, 80)), Rectangle(source="./images/drum.png", pos=(50, 200), size=(80, 80)), Rectangle(source="./images/bass.png", pos=(50, 110), size=(80, 80))]
      self.instrument_index = 0

      # create four instrument loop tracks
      self.tracks = []
      self.tracks.append( LoopTrack((0, Window.height), (Window.width, 100),  "./images/drum.png", (3/255.0, 218/255.0, 246/255.0)) )
      self.tracks.append( LoopTrack((0, Window.height - 100), (Window.width, 100),  "./images/bass.png", (172/255.0, 215/255.0, 3/255.0) ) )
      self.tracks.append( LoopTrack((0, Window.height - 200), (Window.width, 100),  "./images/guitar.png", (238/255.0, 205/255.0, 0.0) ) )
      self.tracks.append( LoopTrack((0, Window.height - 300), (Window.width, 100),  "./images/keyboard.png", (246/255.0, 2/255.0, 115/255.0) ) )

      # now bar
      self.edit_width = Window.width - 100
      self.bar_points = [100, 0, 100, Window.height]
      self.now_bar = Line(points=self.bar_points, width=2)

      # left dividing line
      self.divide_line = Line(points = [100, 0, 100, Window.height], width=2)


   def show(self):
      # show each track
      for t in self.tracks:
        self.add(t)
        t.show()

      self.tracks[0].set_active()

      # add the now bar and dividing line
      self.add(Color(*(.5, .5, .5)))
      self.add(self.now_bar)
      self.add(self.divide_line)


   def hide(self):
      self.remove(self.record_circle_color)
      self.remove(self.record_circle)
      self.remove(self.select_box)
      self.remove(self.instrument_color)
      for instrument in self.instruments:
         self.remove(instrument)


   def set_instrument_index(self, index):
      # set old track to inactive
      self.tracks[self.instrument_index].set_inactive()

      # set new track to active
      self.instrument_index = index
      self.tracks[index].set_active()

      #self.select_box.points = self.select_box_points[self.instrument_index]

   def get_instrument_index(self):
      return self.instrument_index

   def add_blip(self, i, x_frac, y_frac):
      print "adding blip"
      self.tracks[i].add_blip(x_frac, y_frac)


class MainWidget(BaseWidget) :
   def __init__(self):
      super(MainWidget, self).__init__()

      # Debug boolean
      self.debug = False
      self.pause = True

      # basic audio / synth
      self.audio = Audio()
      self.synth = Synth('../FluidR3_GM.sf2')
      self.audio.add_generator(self.synth)

      # basic scheduling
      self.clock = Clock()
      self.cond = Conductor(self.clock)
      self.cond.set_bpm(120)
      self.sched = Scheduler(self.cond)

      # midi instrument settings
      self.instrument_i = 0

      # Create separate midi instruments
      self.midi_instruments = [(0, 128, 0), (0, 0, 34), (1, 0, 36), (0, 0, 1)]
      self.clocks = [Clock(), Clock(), Clock(), Clock()]

      # Create LoopArps
      self.loop_array = []
      self.loops = []
      for p in self.midi_instruments:
         self.loops.append(LoopArpeg(self.synth, self.sched, p[0], p[1], p[2], self.loop_array))
      self.loop_duration = 2000
      self.recording = True

      #l = LoopArpeg(self.synth, self.sched, 0, 0, 1, [(60, 0, 500), (62, 500, 1000), (64, 1000, 1500)]);
      #l.start()

      self.synth.program(*self.midi_instruments[self.instrument_i])
      self.button_number = 27

      # song with Step sequencer as a track
      self.song = Song()

      # tempo
      self.song.cond.set_bpm(120)

      # and text to display our status
      #self.info = Label(text = 'foo', pos = (50, 400), size = (150, 200), valign='top',
      #                 font_size='20sp')
      #self.add_widget(self.info)

      # midi setup
      if not self.debug:
         self.midi_out = open_midi_out("Launchpad")
         self.midi_in = open_midi_in("Launchpad", self.on_midi_in)
         print "setup done"

      # thread setup for higher-resolution song polling
      self.thread = myThread(self.song)
      self.thread.start()
      core.register_terminate_func(self.thread.kill)


      #-------- Graphics --------#
      self.UIGraphics = UIGraphics()
      self.canvas.add(self.UIGraphics)
      self.UIGraphics.show()


   def on_update(self):
      self.sched.on_update()

      #self.info.text = "%d fps\naudio:%s" % (kivyClock.get_fps(), self.audio.get_load())

      now = self.cond.get_tick() % self.loop_duration
      x = float(now)/self.loop_duration * (Window.width - 100) + 100
      self.UIGraphics.now_bar.points = [x, 0, x, Window.height]

      i = self.UIGraphics.get_instrument_index()
      tick = self.clocks[i].get_time() * (120 / 60.) * kTicksPerQuarter

      if tick > self.loop_duration and self.recording:
         self.recording = False

         # recreate loop
         p = self.midi_instruments[i]
         l = LoopArpeg(self.synth, self.sched, p[0], p[1], p[2], self.loop_array);
         l.start()
         self.loop_array = []

   def on_key_down(self, keycode, modifiers):
      if keycode[1] == 'p':
         self.song.toggle()

      if keycode[1] == 'z':
         self.pause = not self.pause
         self.clock.toggle()
         self.clocks[0].toggle()

      if keycode[1] == 'q':
         # full reset of launchpad
         self.midi_out.send_message([176, 0, 0 ])


   # incoming midi message (on a separate thread)
   def on_midi_in(self, message, time_stamp):
      hex_msg = []
      for x in message:
         hex_msg.append(hex(x))

      if len(message) < 1:
         return

      #print message

      # use green and red buttons to change instrument selection
      if len(message) == 2:
         instrument_i = self.UIGraphics.get_instrument_index()
         if message[1] > self.button_number:
            if message[0] == 197:
               self.instrument_i = (instrument_i - 1) % 4
               self.UIGraphics.set_instrument_index(self.instrument_i)
               self.button_number = message[1]
               self.synth.program(*self.midi_instruments[self.instrument_i])

               self.recording = True
               self.clocks[self.instrument_i].toggle()

         elif message[1] < self.button_number:
            if message[0] == 197:
               self.instrument_i = (instrument_i + 1) % 4
               self.UIGraphics.set_instrument_index(self.instrument_i)
               self.button_number = message[1]
               self.synth.program(*self.midi_instruments[self.instrument_i])

               self.recording = True
               self.clocks[self.instrument_i].toggle()
         return

      # parse midi note message
      elif message[2] > 0:
         print self.midi_instruments[self.instrument_i]
         self.synth.program(*self.midi_instruments[self.instrument_i])
         # Play note
         note = message[1]
         velocity = 100
         self.synth.noteon(0, note, velocity)

         # record note
         now = self.sched.cond.get_tick() % self.loop_duration
         note_tuple =  (note, now, now + 1500)
         if self.recording:
            self.loop_array.append(note_tuple)

            x_frac = float(now) / self.loop_duration
            # TODO: change y_frac to depend on the midi note
            y_frac = 0.5
            self.UIGraphics.add_blip(self.instrument_i, x_frac, y_frac)

      cmd, key, vel = message


# A thread class that calls on_update() on a song more frequently so as to have
# smoother, higher-resolution scheduling
class myThread (threading.Thread):
   def __init__(self, song):
      super(myThread, self).__init__()
      self.song = song
      self.active = True

   def kill(self):
      self.active = False
      self.join() # block until thread dies

   def run(self):
      print "Starting Thread"
      while self.active:
         self.song.on_update()
         time.sleep(0.005)
      print "Ending Thread"

# helper for opening a midi port by name
def open_midi_out(name):
   midi_out = rtmidi.MidiOut()
   for i, port_name in enumerate(midi_out.ports):
       #if name in port_name:
       midi_out.open_port(i)
       return midi_out
   raise Exception ("Error: Can't find Midi Out port with name " + name)


# helper for opening a midi port by name
def open_midi_in(name, callback):
   midi_in = rtmidi.MidiIn()
   for i, port_name in enumerate(midi_in.ports):
      midi_in.open_port(i)
      midi_in.callback = callback
      return midi_in
   raise Exception ("Error: Can't find Midi In port with name " + name)

run(MainWidget)
