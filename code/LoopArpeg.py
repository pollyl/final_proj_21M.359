class LoopArpeg():
     def __init__(self, synth, channel, bank, preset, callback = None):
         pass

     def start_recording(self):
         pass

     def add_note(self, note):
         pass

     def stop_recording(self):
         pass

     def _post_at(self, tick):
         self.on_cmd  = self.song.sched.post_at_tick(tick, self._noteon, None)

       def _noteon(self, tick, ignore):
         pitch = self._get_next_pitch()

         # play note on:
         velocity = 60
         self.synth.noteon(self.channel, pitch, velocity)

         # post note-off:
         duration = self.note_len_ratio * self.note_grid
         off_tick = tick + duration
         self.off_cmd = self.song.sched.post_at_tick(off_tick, self._noteoff, pitch)

         # callback:
         if self.callback:
             self.callback(tick, pitch, velocity, duration)

         # post next note. quantize tick to line up with grid of current note length
         tick -= tick % self.note_grid
         next_beat = tick + self.note_grid
         self._post_at(next_beat)

         def _noteoff(self, tick, pitch):
             self.synth.noteoff(self.channel, pitch)
