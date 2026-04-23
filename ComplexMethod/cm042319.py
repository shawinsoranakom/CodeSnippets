def _get_frame_index(animation: Animation, elapsed: float, gap_first: bool = False) -> int:
  """Get the current frame index given elapsed time and animation mode."""
  num_frames = len(animation.frames)
  if num_frames == 1:
    return 0

  fd = animation.frame_duration
  has_backward = animation.mode in (AnimationMode.ONCE_FORWARD_BACKWARD, AnimationMode.REPEAT_FORWARD_BACKWARD)
  repeats = animation.mode in (AnimationMode.REPEAT_FORWARD, AnimationMode.REPEAT_FORWARD_BACKWARD)

  forward_duration = num_frames * fd
  backward_frames = max(num_frames - 2, 0) if has_backward else 0
  hold = animation.hold_end if has_backward else 0.0
  cycle_duration = forward_duration + hold + backward_frames * fd

  if not repeats:
    t = min(elapsed, cycle_duration)
  else:
    t = (elapsed + cycle_duration if gap_first else elapsed) % animation.repeat_interval

  # Forward phase
  if t < forward_duration:
    return min(int(t / fd), num_frames - 1)
  t -= forward_duration

  # Hold at last frame
  if t < hold:
    return num_frames - 1
  t -= hold

  # Backward phase
  if backward_frames and t < backward_frames * fd:
    return num_frames - 2 - min(int(t / fd), backward_frames - 1)

  return 0 if has_backward else num_frames - 1