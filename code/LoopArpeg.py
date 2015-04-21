from clock_lec import kTicksPerQuarter
from song_lec import *

class LoopArpeg(Track):
     def __init__(self, synth, sched, channel, bank, preset, callback = None):
         super(LoopArpeg, self).__init__()
         self.bank = bank
         self.channel = channel
         self.preset = preset
         self.sched = sched

         # Set sequence of notes
         self.notes = [(60, 1000, 2000), (62, 3000, 4000)]
         self.loop_length = 4

         # output parameters
         self.synth = synth
         self.channel = channel
         self.cbp = (channel, bank, preset)
         self.callback = callback

         # run-time variables
         self.cur_idx = 0
         self.on_cmd = None
         self.off_cmd = None

     def start_recording(self):
         pass

     def add_note(self, note):
         pass

     def stop_recording(self):
         pass

     def start(self):
         self.synth.program(self.channel, self.bank, self.preset)
         now = self.sched.cond.get_tick()

         # Post the first note on
         i = (self.cur_idx + 1) % len(self.notes)
         next_tuple = self.notes[i]
         next_on_tick = next_tuple[1]
         self._post_at(next_on_tick)

     def stop(self):
        if self.note_on is not None:
             self.sched.remove(self.note_on)

        if self.note_off is not None:
             self.sched.remove(self.note_off)
             self.note_off.execute()

     def _get_next_pitch(self):
         # advance index
         pitch = self.notes[self.cur_idx]
         notes_len = len(self.notes)
         self.cur_idx += 1

         # keep in bounds:
         self.cur_idx = self.cur_idx % notes_len

         return pitch

     def _post_at(self, tick):
         print "posted"
         self.on_cmd  = self.sched.post_at_tick(tick, self._noteon, None)

     def _noteon(self, tick, ignore):
         print "note on"
         print self.cur_idx
         pitch_tuple = self._get_next_pitch()
         pitch = pitch_tuple[0]

         # play note on:
         velocity = 60
         self.synth.noteon(self.channel, pitch, velocity)

         # post note-off:
         duration = pitch_tuple[2] - pitch_tuple[1]
         off_tick = tick + duration
         self.off_cmd = self.sched.post_at_tick(off_tick, self._noteoff, pitch)

         # callback:
         if self.callback:
             self.callback(tick, pitch, velocity, duration)

         # post next note. quantize tick to line up with grid of current note length
         #tick -= tick % self.note_grid
         #next_beat = tick + self.note_grid
         i = (self.cur_idx + 1) % len(self.notes)
         next_tuple = self.notes[i]
         next_on_tick = next_tuple[1]
         self._post_at(next_on_tick)

     def _noteoff(self, tick, pitch):
         print "note off"
         self.synth.noteoff(self.channel, pitch)
