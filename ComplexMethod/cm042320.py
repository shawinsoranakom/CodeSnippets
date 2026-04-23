def get_dots(self) -> list[tuple[int, int]]:
    now = time.monotonic()
    elapsed = now - self._start_time

    # Handle rewind for forward-only animations
    if self._rewinding:
      rewind_elapsed = now - self._rewind_start
      frames_back = round(rewind_elapsed / self._animation.frame_duration)
      frame_index = self._rewind_from - frames_back
      if frame_index <= 0:
        return self._switch_to_next(now)
      return self._animation.frames[frame_index]

    # Play starting frames first (once)
    starting = self._animation.starting_frames or []
    starting_duration = len(starting) * self._animation.frame_duration
    if starting and elapsed < starting_duration:
      frame_index = min(int(elapsed / self._animation.frame_duration), len(starting) - 1)
      return starting[frame_index]

    # Main loop
    loop_elapsed = elapsed - starting_duration if starting else elapsed
    frame_index = _get_frame_index(self._animation, loop_elapsed, gap_first=bool(starting))

    if frame_index != 0:
      self._seen_nonzero = True

    if self._next is not None:
      if frame_index == 0 and (len(self._animation.frames) == 1 or self._seen_nonzero):
        return self._switch_to_next(now)
      # No natural return to frame 0 — start rewinding
      if self._animation.mode in (AnimationMode.ONCE_FORWARD, AnimationMode.REPEAT_FORWARD):
        self._rewinding = True
        self._rewind_start = now
        self._rewind_from = frame_index

    return self._animation.frames[frame_index]