def resize_and_crop_image(
    image,
    desired_size,
    padded_size,
    aug_scale_min=1.0,
    aug_scale_max=1.0,
    seed=1,
    method=tf.image.ResizeMethod.BILINEAR,
    keep_aspect_ratio=True,
    centered_crop=False,
):
  """Resizes the input image to output size (RetinaNet style).

  Resize and pad images given the desired output size of the image and
  stride size.

  Here are the preprocessing steps.
  1. For a given image, keep its aspect ratio and rescale the image to make it
     the largest rectangle to be bounded by the rectangle specified by the
     `desired_size`.
  2. Pad the rescaled image to the padded_size.

  Args:
    image: a `Tensor` of shape [height, width, c] representing an image.
    desired_size: a `Tensor` or `int` list/tuple of two elements representing
      [height, width] of the desired actual output image size.
    padded_size: a `Tensor` or `int` list/tuple of two elements representing
      [height, width] of the padded output image size. Padding will be applied
      after scaling the image to the desired_size. Can be None to disable
      padding.
    aug_scale_min: a `float` with range between [0, 1.0] representing minimum
      random scale applied to desired_size for training scale jittering.
    aug_scale_max: a `float` with range between [1.0, inf] representing maximum
      random scale applied to desired_size for training scale jittering.
    seed: seed for random scale jittering.
    method: function to resize input image to scaled image.
    keep_aspect_ratio: whether or not to keep the aspect ratio when resizing.
    centered_crop: If `centered_crop` is set to True, then resized crop (if
      smaller than padded size) is place in the center of the image. Default
      behaviour is to place it at left top corner.

  Returns:
    output_image: `Tensor` of shape [height, width, c] where [height, width]
      equals to `output_size`.
    image_info: a 2D `Tensor` that encodes the information of the image and the
      applied preprocessing. It is in the format of
      [[original_height, original_width], [desired_height, desired_width],
       [y_scale, x_scale], [y_offset, x_offset]], where [desired_height,
      desired_width] is the actual scaled image size, and [y_scale, x_scale] is
      the scaling factor, which is the ratio of
      scaled dimension / original dimension.
  """
  with tf.name_scope('resize_and_crop_image'):
    image_size = tf.cast(tf.shape(image)[0:2], tf.float32)

    random_jittering = (
        isinstance(aug_scale_min, tf.Tensor)
        or isinstance(aug_scale_max, tf.Tensor)
        or not math.isclose(aug_scale_min, 1.0)
        or not math.isclose(aug_scale_max, 1.0)
    )

    if random_jittering:
      random_scale = tf.random.uniform(
          [], aug_scale_min, aug_scale_max, seed=seed
      )
      scaled_size = tf.round(random_scale * tf.cast(desired_size, tf.float32))
    else:
      scaled_size = tf.cast(desired_size, tf.float32)

    if keep_aspect_ratio:
      scale = tf.minimum(
          scaled_size[0] / image_size[0], scaled_size[1] / image_size[1]
      )
      scaled_size = tf.round(image_size * scale)

    # Computes 2D image_scale.
    image_scale = scaled_size / image_size

    # Selects non-zero random offset (x, y) if scaled image is larger than
    # desired_size.
    if random_jittering:
      max_offset = scaled_size - tf.cast(desired_size, tf.float32)
      max_offset = tf.where(
          tf.less(max_offset, 0), tf.zeros_like(max_offset), max_offset
      )
      offset = max_offset * tf.random.uniform(
          [
              2,
          ],
          0,
          1,
          seed=seed,
      )
      offset = tf.cast(offset, tf.int32)
    else:
      offset = tf.zeros((2,), tf.int32)

    scaled_image = tf.image.resize(
        image, tf.cast(scaled_size, tf.int32), method=method
    )

    if random_jittering:
      scaled_image = scaled_image[
          offset[0] : offset[0] + desired_size[0],
          offset[1] : offset[1] + desired_size[1],
          :,
      ]

    output_image = scaled_image
    if padded_size is not None:
      if centered_crop:
        scaled_image_size = tf.cast(tf.shape(scaled_image)[0:2], tf.int32)
        output_image = tf.image.pad_to_bounding_box(
            scaled_image,
            tf.maximum((padded_size[0] - scaled_image_size[0]) // 2, 0),
            tf.maximum((padded_size[1] - scaled_image_size[1]) // 2, 0),
            padded_size[0],
            padded_size[1],
        )
      else:
        output_image = tf.image.pad_to_bounding_box(
            scaled_image, 0, 0, padded_size[0], padded_size[1]
        )

    image_info = tf.stack([
        image_size,
        tf.cast(desired_size, dtype=tf.float32),
        image_scale,
        tf.cast(offset, tf.float32),
    ])
    return output_image, image_info