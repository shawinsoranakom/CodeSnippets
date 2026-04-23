def resize_and_jitter_image(image,
                            desired_size,
                            jitter=0.0,
                            letter_box=None,
                            random_pad=True,
                            crop_only=False,
                            shiftx=0.5,
                            shifty=0.5,
                            cut=None,
                            method=tf.image.ResizeMethod.BILINEAR,
                            seed=None):
  """Resize, Pad, and distort a given input image.

  Args:
    image: a `Tensor` of shape [height, width, 3] representing an image.
    desired_size: a `Tensor` or `int` list/tuple of two elements representing
      [height, width] of the desired actual output image size.
    jitter: an `int` representing the maximum jittering that can be applied to
      the image.
    letter_box: a `bool` representing if letterboxing should be applied.
    random_pad: a `bool` representing if random padding should be applied.
    crop_only: a `bool` representing if only cropping will be applied.
    shiftx: a `float` indicating if the image is in the left or right.
    shifty: a `float` value indicating if the image is in the top or bottom.
    cut: a `float` value indicating the desired center of the final patched
      image.
    method: function to resize input image to scaled image.
    seed: seed for random scale jittering.

  Returns:
    image_: a `Tensor` of shape [height, width, 3] where [height, width]
      equals to `desired_size`.
    infos: a 2D `Tensor` that encodes the information of the image and the
      applied preprocessing. It is in the format of
      [[original_height, original_width], [desired_height, desired_width],
        [y_scale, x_scale], [y_offset, x_offset]], where [desired_height,
      desired_width] is the actual scaled image size, and [y_scale, x_scale] is
      the scaling factor, which is the ratio of
      scaled dimension / original dimension.
    cast([original_width, original_height, width, height, ptop, pleft, pbottom,
      pright], tf.float32): a `Tensor` containing the information of the image
        andthe applied preprocessing.
  """

  def intersection(a, b):
    """Finds the intersection between 2 crops."""
    minx = tf.maximum(a[0], b[0])
    miny = tf.maximum(a[1], b[1])
    maxx = tf.minimum(a[2], b[2])
    maxy = tf.minimum(a[3], b[3])
    return tf.convert_to_tensor([minx, miny, maxx, maxy])

  def cast(values, dtype):
    return [tf.cast(value, dtype) for value in values]

  if jitter > 0.5 or jitter < 0:
    raise ValueError('maximum change in aspect ratio must be between 0 and 0.5')

  with tf.name_scope('resize_and_jitter_image'):
    # Cast all parameters to a usable float data type.
    jitter = tf.cast(jitter, tf.float32)
    original_dtype, original_dims = image.dtype, tf.shape(image)[:2]

    # original width, original height, desigered width, desired height
    original_width, original_height, width, height = cast(
        [original_dims[1], original_dims[0], desired_size[1], desired_size[0]],
        tf.float32)

    # Compute the random delta width and height etc. and randomize the
    # location of the corner points.
    jitter_width = original_width * jitter
    jitter_height = original_height * jitter
    pleft = random_uniform_strong(
        -jitter_width, jitter_width, jitter_width.dtype, seed=seed)
    pright = random_uniform_strong(
        -jitter_width, jitter_width, jitter_width.dtype, seed=seed)
    ptop = random_uniform_strong(
        -jitter_height, jitter_height, jitter_height.dtype, seed=seed)
    pbottom = random_uniform_strong(
        -jitter_height, jitter_height, jitter_height.dtype, seed=seed)

    # Letter box the image.
    if letter_box:
      (image_aspect_ratio,
       input_aspect_ratio) = original_width / original_height, width / height
      distorted_aspect = image_aspect_ratio / input_aspect_ratio

      delta_h, delta_w = 0.0, 0.0
      pullin_h, pullin_w = 0.0, 0.0
      if distorted_aspect > 1:
        delta_h = ((original_width / input_aspect_ratio) - original_height) / 2
      else:
        delta_w = ((original_height * input_aspect_ratio) - original_width) / 2

      ptop = ptop - delta_h - pullin_h
      pbottom = pbottom - delta_h - pullin_h
      pright = pright - delta_w - pullin_w
      pleft = pleft - delta_w - pullin_w

    # Compute the width and height to crop or pad too, and clip all crops to
    # to be contained within the image.
    swidth = original_width - pleft - pright
    sheight = original_height - ptop - pbottom
    src_crop = intersection([ptop, pleft, sheight + ptop, swidth + pleft],
                            [0, 0, original_height, original_width])

    # Random padding used for mosaic.
    h_ = src_crop[2] - src_crop[0]
    w_ = src_crop[3] - src_crop[1]
    if random_pad:
      rmh = tf.maximum(0.0, -ptop)
      rmw = tf.maximum(0.0, -pleft)
    else:
      rmw = (swidth - w_) * shiftx
      rmh = (sheight - h_) * shifty

    # Cast cropping params to usable dtype.
    src_crop = tf.cast(src_crop, tf.int32)

    # Compute padding parmeters.
    dst_shape = [rmh, rmw, rmh + h_, rmw + w_]
    ptop, pleft, pbottom, pright = dst_shape
    pad = dst_shape * tf.cast([1, 1, -1, -1], ptop.dtype)
    pad += tf.cast([0, 0, sheight, swidth], ptop.dtype)
    pad = tf.cast(pad, tf.int32)

    infos = []

    # Crop the image to desired size.
    cropped_image = tf.slice(
        image, [src_crop[0], src_crop[1], 0],
        [src_crop[2] - src_crop[0], src_crop[3] - src_crop[1], -1])
    crop_info = tf.stack([
        tf.cast(original_dims, tf.float32),
        tf.cast(tf.shape(cropped_image)[:2], dtype=tf.float32),
        tf.ones_like(original_dims, dtype=tf.float32),
        tf.cast(src_crop[:2], tf.float32)
    ])
    infos.append(crop_info)

    if crop_only:
      if not letter_box:
        h_, w_ = cast(get_image_shape(cropped_image), width.dtype)
        width = tf.cast(tf.round((w_ * width) / swidth), tf.int32)
        height = tf.cast(tf.round((h_ * height) / sheight), tf.int32)
        cropped_image = tf.image.resize(
            cropped_image, [height, width], method=method)
        cropped_image = tf.cast(cropped_image, original_dtype)
      return cropped_image, infos, cast([
          original_width, original_height, width, height, ptop, pleft, pbottom,
          pright
      ], tf.int32)

    # Pad the image to desired size.
    image_ = tf.pad(
        cropped_image, [[pad[0], pad[2]], [pad[1], pad[3]], [0, 0]],
        constant_values=PAD_VALUE)

    # Pad and scale info
    isize = tf.cast(tf.shape(image_)[:2], dtype=tf.float32)
    osize = tf.cast((desired_size[0], desired_size[1]), dtype=tf.float32)
    pad_info = tf.stack([
        tf.cast(tf.shape(cropped_image)[:2], tf.float32),
        osize,
        osize/isize,
        (-tf.cast(pad[:2], tf.float32)*osize/isize)
    ])
    infos.append(pad_info)

    temp = tf.shape(image_)[:2]
    cond = temp > tf.cast(desired_size, temp.dtype)
    if tf.reduce_any(cond):
      size = tf.cast(desired_size, temp.dtype)
      size = tf.where(cond, size, temp)
      image_ = tf.image.resize(
          image_, (size[0], size[1]), method=tf.image.ResizeMethod.AREA)
      image_ = tf.cast(image_, original_dtype)

    image_ = tf.image.resize(
        image_, (desired_size[0], desired_size[1]),
        method=tf.image.ResizeMethod.BILINEAR,
        antialias=False)

    image_ = tf.cast(image_, original_dtype)
    if cut is not None:
      image_, crop_info = mosaic_cut(image_, original_width, original_height,
                                     width, height, cut, ptop, pleft, pbottom,
                                     pright, shiftx, shifty)
      infos.append(crop_info)
    return image_, infos, cast([
        original_width, original_height, width, height, ptop, pleft, pbottom,
        pright
    ], tf.float32)