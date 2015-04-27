from clock import kTicksPerQuarter
from song import *

class LoopArpeg(Track):
     def __init__(self, synth, sched, channel, bank, preset, notes, callback = None):
         super(LoopArpeg, self).__init__()
         self.bank = bank
         self.channel = channel
         self.preset = preset
         self.sched = sched

         # Set sequence of notes
         self.notes = notes#[(60, 0, 250), (62, 1, 1000), (64, 500, 1500), (65, 1500, 2000)]

         # looping info
         self.loops = 0
         self.offset = self.sched.cond.get_tick()
         self.loop_duration = 2000

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

         if len(self.notes) == 0:
            return

         self.offset = self.sched.cond.get_tick()
         next_tuple = self.notes[self.cur_idx]
         next_on_tick = self.offset + next_tuple[1]

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
         if self.cur_idx >= notes_len:
            self.cur_idx = self.cur_idx % notes_len

         return pitch

     def _post_at(self, tick):
         self.on_cmd  = self.sched.post_at_tick(tick, self._noteon, None)

     def _noteon(self, tick, ignore):
         pitch_tuple = self._get_next_pitch()
         pitch = pitch_tuple[0]

         if self.cur_idx == 0:
            self.loops += 1

         # play note on:
         velocity = 100
         self.synth.program(self.channel, self.bank, self.preset)
         self.synth.noteon(self.channel, pitch, velocity)

         # post note-off:
         #duration = pitch_tuple[2] - pitch_tuple[1]
         #off_tick = tick + duration + self.offset
         off_tick = (self.loops * self.loop_duration) + self.offset + pitch_tuple[2]
         self.off_cmd = self.sched.post_at_tick(off_tick, self._noteoff, pitch)

         # callback:
         if self.callback:
             self.callback(tick, pitch, velocity, duration)

         # post next note. quantize tick to line up with grid of current note length
         #tick -= tick % self.note_grid
         #next_beat = tick + self.note_grid
         #i = (self.cur_idx + 1) % len(self.notes)
         i = self.cur_idx
         next_tuple = self.notes[i]
         next_on_tick = self.loops * self.loop_duration + next_tuple[1] + self.offset
         self._post_at(next_on_tick)

     def _noteoff(self, tick, pitch):
         self.synth.noteoff(self.channel, pitch)

     def now_str(self):
         return ""#return str(self.notes[self.cur_idx])
