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


   def show(self):
      self.add(self.record_circle_color)
      self.select_box.points = self.select_box_points[self.instrument_index]
      self.add(self.select_box)
      self.add(self.record_circle)
      self.add(self.instrument_color)
      for instrument in self.instruments:
         self.add(instrument)


   def hide(self):
      self.remove(self.record_circle_color)
      self.remove(self.record_circle)
      self.remove(self.select_box)
      self.remove(self.instrument_color)
      for instrument in self.instruments:
         self.remove(instrument)


   def set_instrument_index(self, index):
      self.instrument_index = index
      self.select_box.points = self.select_box_points[self.instrument_index]

   def get_instrument_index(self):
      return self.instrument_index



class MainWidget(BaseWidget) :
   def __init__(self):
      super(MainWidget, self).__init__()

      # basic audio / synth
      self.audio = Audio()
      self.synth = Synth('../FluidR3_GM.sf2')
      self.audio.add_generator(self.synth)

      # midi instrument settings
      self.instrument_i = 0
      self.midi_instruments = [(0, 0, 27), (0, 0, 1), (0, 128, 0), (0, 0, 36)]
      self.synth.program(*self.midi_instruments[self.instrument_i])
      self.button_number = 27

      # song with Step sequencer as a track
      self.song = Song()
      #self.song.add_track( Metronome( self.synth ) )
      # self.step = StepSequencer(self.synth, (35, 40, 42), 8, self.on_step_callback)
      # self.song.add_track( self.step )

      # tempo
      self.song.cond.set_bpm(120)

      # and text to display our status
      self.info = Label(text = 'foo', pos = (50, 400), size = (150, 200), valign='top',
                        font_size='20sp')
      self.add_widget(self.info)

      # midi setup
      self.midi_out = open_midi_out("Launchpad")
      self.midi_in = open_midi_in("Launchpad", self.on_midi_in)

      # thread setup for higher-resolution song polling
      self.thread = myThread(self.song)
      self.thread.start()
      core.register_terminate_func(self.thread.kill)


      #-------- Graphics --------#
      self.UIGraphics = UIGraphics()
      self.canvas.add(self.UIGraphics)
      self.UIGraphics.show()



   def on_update(self) :
      self.info.text = "%d fps\naudio:%s" % (kivyClock.get_fps(), self.audio.get_load())

   # callback from the step sequencer
   def on_step_callback(self, step, hits):
      # turn on all hits at this step
      for h in hits:
         key = launch_xy_to_key(step, h)
         self.midi_out.send_message([144, key, 15])

      # schedule hits to turn off a bit later.
      if len(hits):
         now = self.song.cond.get_tick()
         self.song.sched.post_at_tick(now + 240, self._launch_off, (step, hits))

   # turn a button off a bit after it was turned on
   def _launch_off(self, tick, arg):
      step, hits = arg
      for h in hits:
         self._set_color(step, h)

   def on_key_down(self, keycode, modifiers):
      if keycode[1] == 'p':
         self.song.toggle()

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
      
      print message
      
      # use green and red buttons to change instrument selection
      if len(message) == 2:
         instrument_i = self.UIGraphics.get_instrument_index()
         if message[1] > self.button_number:
            if message[0] == 197:
               self.instrument_i = (instrument_i - 1) % 4
               self.UIGraphics.set_instrument_index(self.instrument_i)
               self.button_number = message[1]
               self.synth.program(*self.midi_instruments[self.instrument_i])
         elif message[1] < self.button_number:
            if message[0] == 197:
               self.instrument_i = (instrument_i + 1) % 4
               self.UIGraphics.set_instrument_index(self.instrument_i)
               self.button_number = message[1]
               self.synth.program(*self.midi_instruments[self.instrument_i])
         return

      if message[2] > 0:
         self.synth.noteon(0, message[1], 100)

      cmd, key, vel = message

      # only listen to note-on msgs:
      if cmd != 144:
         return

      # control the step sequencer:
      x, y = launch_key_to_xy(key)
      if x < 8 and y < 3:
         if vel > 0:
            self.step.toggle(x, y)
            self._set_color(x, y)
         return

      # otherwise, just flash buttons
      color = [12, 60][vel > 0]
      self.midi_out.send_message([144, key, color])

   # helper function for setting the correct color on a launchpad button
   def _set_color(self, x, y):
      key = launch_xy_to_key(x, y)
      color = [12, 62][self.step.get(x, y)]
      self.midi_out.send_message([144, key, color])


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


# Implements a step sequencer.
# width is # of steps
# pitches is a list of pitches. Length of list is height of sequencer.
# callback(step, hits) is called on every step with the list of indicies
# that are active on at that step.
class StepSequencer(Track):
   def __init__(self, synth, pitches, width, callback = None):
      super(StepSequencer, self).__init__()
      self.synth = synth
      self.cmd = None
      self.beat_len = kTicksPerQuarter / 4

      self.width = width
      self.pitches = pitches
      self.callback = callback

      self.step = 0
      self.hits = np.zeros((width, len(pitches)), dtype=np.int)

      # pick a drum patch
      synth.program(0 , 128, 0)

   def start(self):
      now = self.song.cond.get_tick()
      next_beat = now - (now % kTicksPerQuarter) + kTicksPerQuarter
      self.cmd = self.song.sched.post_at_tick(next_beat, self._hit, [])

   def stop(self):
      if self.cmd:
         self.song.sched.remove(self.cmd)
      # turn off everything
      for p in pitches:
         self.synth.noteoff(0, p)

   def set(self, x, y, val):
      self.hits[x,y] = val

   def get(self, x, y):
      return self.hits[x,y]

   def toggle(self, x, y):
      self.hits[x,y] = 1 - self.hits[x,y]

   # gets called every step. last_pitches is the list of active notes from the last step
   def _hit(self, tick, last_pitches):
      for p in last_pitches:
         self.synth.noteoff(0, p)

      # get the list of active notes for this step
      indicies = [i for i,n in enumerate(self.hits[self.step]) if n]
      pitches = [self.pitches[n] for n in indicies]

      # turn on notes
      for p in pitches:
         self.synth.noteon(0, p, 100)

      # callback is called
      if self.callback:
         self.callback(self.step, indicies)

      # set up for next step
      self.cmd = self.song.sched.post_at_tick(tick + self.beat_len, self._hit, pitches)
      self.step = (self.step + 1) % self.width


# convert the midi key into x,y where (0,0) is the bottom left corner
# of the launchpad
def launch_key_to_xy(key):
   div, mod = divmod(key, 16)
   return mod, 7-div


# convert x,y to the MIDI key number
def launch_xy_to_key(x,y):
   return x + (7-y) * 16


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
