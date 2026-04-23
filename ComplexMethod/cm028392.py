def resize_to_range(image,
                    label=None,
                    min_size=None,
                    max_size=None,
                    factor=None,
                    keep_aspect_ratio=True,
                    align_corners=True,
                    label_layout_is_chw=False,
                    scope=None,
                    method=tf.image.ResizeMethod.BILINEAR):
  """Resizes image or label so their sides are within the provided range.

  The output size can be described by two cases:
  1. If the image can be rescaled so its minimum size is equal to min_size
     without the other side exceeding max_size, then do so.
  2. Otherwise, resize so the largest side is equal to max_size.

  An integer in `range(factor)` is added to the computed sides so that the
  final dimensions are multiples of `factor` plus one.

  Args:
    image: A 3D tensor of shape [height, width, channels].
    label: (optional) A 3D tensor of shape [height, width, channels] (default)
      or [channels, height, width] when label_layout_is_chw = True.
    min_size: (scalar) desired size of the smaller image side.
    max_size: (scalar) maximum allowed size of the larger image side. Note
      that the output dimension is no larger than max_size and may be slightly
      smaller than max_size when factor is not None.
    factor: Make output size multiple of factor plus one.
    keep_aspect_ratio: Boolean, keep aspect ratio or not. If True, the input
      will be resized while keeping the original aspect ratio. If False, the
      input will be resized to [max_resize_value, max_resize_value] without
      keeping the original aspect ratio.
    align_corners: If True, exactly align all 4 corners of input and output.
    label_layout_is_chw: If true, the label has shape [channel, height, width].
      We support this case because for some instance segmentation dataset, the
      instance segmentation is saved as [num_instances, height, width].
    scope: Optional name scope.
    method: Image resize method. Defaults to tf.image.ResizeMethod.BILINEAR.

  Returns:
    A 3-D tensor of shape [new_height, new_width, channels], where the image
    has been resized (with the specified method) so that
    min(new_height, new_width) == ceil(min_size) or
    max(new_height, new_width) == ceil(max_size).

  Raises:
    ValueError: If the image is not a 3D tensor.
  """
  with tf.name_scope(scope, 'resize_to_range', [image]):
    new_tensor_list = []
    min_size = tf.cast(min_size, tf.float32)
    if max_size is not None:
      max_size = tf.cast(max_size, tf.float32)
      # Modify the max_size to be a multiple of factor plus 1 and make sure the
      # max dimension after resizing is no larger than max_size.
      if factor is not None:
        max_size = (max_size - (max_size - 1) % factor)

    [orig_height, orig_width, _] = resolve_shape(image, rank=3)
    orig_height = tf.cast(orig_height, tf.float32)
    orig_width = tf.cast(orig_width, tf.float32)
    orig_min_size = tf.minimum(orig_height, orig_width)

    # Calculate the larger of the possible sizes
    large_scale_factor = min_size / orig_min_size
    large_height = tf.cast(tf.floor(orig_height * large_scale_factor), tf.int32)
    large_width = tf.cast(tf.floor(orig_width * large_scale_factor), tf.int32)
    large_size = tf.stack([large_height, large_width])

    new_size = large_size
    if max_size is not None:
      # Calculate the smaller of the possible sizes, use that if the larger
      # is too big.
      orig_max_size = tf.maximum(orig_height, orig_width)
      small_scale_factor = max_size / orig_max_size
      small_height = tf.cast(
          tf.floor(orig_height * small_scale_factor), tf.int32)
      small_width = tf.cast(tf.floor(orig_width * small_scale_factor), tf.int32)
      small_size = tf.stack([small_height, small_width])
      new_size = tf.cond(
          tf.cast(tf.reduce_max(large_size), tf.float32) > max_size,
          lambda: small_size,
          lambda: large_size)
    # Ensure that both output sides are multiples of factor plus one.
    if factor is not None:
      new_size += (factor - (new_size - 1) % factor) % factor
    if not keep_aspect_ratio:
      # If not keep the aspect ratio, we resize everything to max_size, allowing
      # us to do pre-processing without extra padding.
      new_size = [tf.reduce_max(new_size), tf.reduce_max(new_size)]
    new_tensor_list.append(tf.image.resize(
        image, new_size, method=method, align_corners=align_corners))
    if label is not None:
      if label_layout_is_chw:
        # Input label has shape [channel, height, width].
        resized_label = tf.expand_dims(label, 3)
        resized_label = tf.image.resize(
            resized_label,
            new_size,
            method=get_label_resize_method(label),
            align_corners=align_corners)
        resized_label = tf.squeeze(resized_label, 3)
      else:
        # Input label has shape [height, width, channel].
        resized_label = tf.image.resize(
            label,
            new_size,
            method=get_label_resize_method(label),
            align_corners=align_corners)
      new_tensor_list.append(resized_label)
    else:
      new_tensor_list.append(None)
    return new_tensor_list