def _denormalize_images(images: tf.Tensor) -> tf.Tensor:
    if image_mean is None and image_std is None:
      images *= tf.constant(
          preprocess_ops.STDDEV_RGB, shape=[1, 1, 3], dtype=images.dtype
      )
      images += tf.constant(
          preprocess_ops.MEAN_RGB, shape=[1, 1, 3], dtype=images.dtype
      )
    elif image_mean is not None and image_std is not None:
      if isinstance(image_mean, float) and isinstance(image_std, float):
        images = images * image_std + image_mean
      elif isinstance(image_mean, list) and isinstance(image_std, list):
        images *= tf.constant(image_std, shape=[1, 1, 3], dtype=images.dtype)
        images += tf.constant(image_mean, shape=[1, 1, 3], dtype=images.dtype)
      else:
        raise ValueError(
            '`image_mean` and `image_std` should be the same type.'
        )
    else:
      raise ValueError(
          'Both `image_mean` and `image_std` should be set or None at the same '
          'time.'
      )
    return tf.cast(images, dtype=tf.uint8)