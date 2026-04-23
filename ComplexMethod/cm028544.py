def frame_pooling(frames, method="average", num_frames=None):
  """Pools over the frames of a video.

  Args:
    frames: tensor of shape [batch_size, num_frames, feature_size].
    method: string indicating pooling method, one of: "average", "max",
      "attention", or "none".
    num_frames: optional tensor of shape [batch_size] indicating valid number of
      frames for each video.

  Returns:
    tensor of shape [batch_size, feature_size] for average, max, or
    attention pooling, and shape [batch_size*num_frames, feature_size]
    for none pooling.
  Raises:
    ValueError: if method is other than "average", "max", "attention", or
    "none".
  """
  frame_mask = None
  if num_frames is not None:
    max_frames = frames.shape.as_list()[1]
    # Generate binary mask from number of frames.
    frame_mask = tf.sequence_mask(num_frames, max_frames, frames.dtype)
    frame_mask = tf.expand_dims(frame_mask, axis=2)

  if method == "average":
    if num_frames is None:
      reduced = tf.reduce_mean(frames, 1)
    else:
      num_frames = tf.reshape(tf.cast(num_frames, frames.dtype), [-1, 1])
      reduced = tf.reduce_sum(frames * frame_mask, 1) / num_frames
  elif method == "max":
    if num_frames is not None:
      frame_mask = tf.cast(frame_mask, tf.bool)
      frames = tf.where(
          frame_mask,
          frames,
          tf.ones_like(frames, dtype=frames.dtype)
          * _large_compatible_negative(frames.dtype),
      )
    # Magic to avoid loss NaN when bfloat16 is enabled.
    # See yaqs/5377152819545505792 and b/214396297 for more discussion.
    reduced = tf.reduce_max(frames, 1) + tf.reduce_mean(frames, 1) * 0
  elif method == "swap":
    # Note we assume the frames are in the shape of
    # [batch_size, num_frames, feature_size]. Otherwise this function might
    # fail.
    reduced = frame_swap(frames, frame_mask)
  elif method == "none":
    feature_size = frames.shape.as_list()[2]
    reduced = tf.reshape(frames, [-1, feature_size])
  else:
    raise ValueError("Unrecognized pooling method: %s" % method)

  return reduced