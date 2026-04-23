def mosaic_cut(image, original_width, original_height, width, height, center,
               ptop, pleft, pbottom, pright, shiftx, shifty):
  """Generates a random center location to use for the mosaic operation.

  Given a center location, cuts the input image into a slice that will be
  concatenated with other slices with the same center in order to construct
  a final mosaicked image.

  Args:
    image: `Tensor` of shape [None, None, 3] that needs to be altered.
    original_width: `float` value indicating the original width of the image.
    original_height: `float` value indicating the original height of the image.
    width: `float` value indicating the final width of the image.
    height: `float` value indicating the final height of the image.
    center: `float` value indicating the desired center of the final patched
      image.
    ptop: `float` value indicating the top of the image without padding.
    pleft: `float` value indicating the left of the image without padding.
    pbottom: `float` value indicating the bottom of the image without padding.
    pright: `float` value indicating the right of the image without padding.
    shiftx: `float` 0.0 or 1.0 value indicating if the image is on the left or
      right.
    shifty: `float` 0.0 or 1.0 value indicating if the image is at the top or
      bottom.

  Returns:
    image: The cropped image in the same datatype as the input image.
    crop_info: `float` tensor that is applied to the boxes in order to select
      the boxes still contained within the image.
  """

  def cast(values, dtype):
    return [tf.cast(value, dtype) for value in values]

  with tf.name_scope('mosaic_cut'):
    center = tf.cast(center, width.dtype)
    zero = tf.cast(0.0, width.dtype)
    cut_x, cut_y = center[1], center[0]

    # Select the crop of the image to use
    left_shift = tf.minimum(
        tf.minimum(cut_x, tf.maximum(zero, -pleft * width / original_width)),
        width - cut_x)
    top_shift = tf.minimum(
        tf.minimum(cut_y, tf.maximum(zero, -ptop * height / original_height)),
        height - cut_y)
    right_shift = tf.minimum(
        tf.minimum(width - cut_x,
                   tf.maximum(zero, -pright * width / original_width)), cut_x)
    bot_shift = tf.minimum(
        tf.minimum(height - cut_y,
                   tf.maximum(zero, -pbottom * height / original_height)),
        cut_y)

    (left_shift, top_shift, right_shift, bot_shift,
     zero) = cast([left_shift, top_shift, right_shift, bot_shift, zero],
                  tf.float32)
    # Build a crop offset and a crop size tensor to use for slicing.
    crop_offset = [zero, zero, zero]
    crop_size = [zero - 1, zero - 1, zero - 1]
    if shiftx == 0.0 and shifty == 0.0:
      crop_offset = [top_shift, left_shift, zero]
      crop_size = [cut_y, cut_x, zero - 1]
    elif shiftx == 1.0 and shifty == 0.0:
      crop_offset = [top_shift, cut_x - right_shift, zero]
      crop_size = [cut_y, width - cut_x, zero - 1]
    elif shiftx == 0.0 and shifty == 1.0:
      crop_offset = [cut_y - bot_shift, left_shift, zero]
      crop_size = [height - cut_y, cut_x, zero - 1]
    elif shiftx == 1.0 and shifty == 1.0:
      crop_offset = [cut_y - bot_shift, cut_x - right_shift, zero]
      crop_size = [height - cut_y, width - cut_x, zero - 1]

    # Contain and crop the image.
    ishape = tf.cast(tf.shape(image)[:2], crop_size[0].dtype)
    crop_size[0] = tf.minimum(crop_size[0], ishape[0])
    crop_size[1] = tf.minimum(crop_size[1], ishape[1])

    crop_offset = tf.cast(crop_offset, tf.int32)
    crop_size = tf.cast(crop_size, tf.int32)

    image = tf.slice(image, crop_offset, crop_size)
    crop_info = tf.stack([
        tf.cast(ishape, tf.float32),
        tf.cast(tf.shape(image)[:2], dtype=tf.float32),
        tf.ones_like(ishape, dtype=tf.float32),
        tf.cast(crop_offset[:2], tf.float32)
    ])

  return image, crop_info