def _parse_train_image(self, decoded_tensors):
    """Parses image data for training."""
    image_bytes = decoded_tensors[self._image_field_key]
    require_decoding = (
        not tf.is_tensor(image_bytes) or image_bytes.dtype == tf.dtypes.string
    )

    if (
        require_decoding
        and self._decode_jpeg_only
        and self._aug_crop
    ):
      image_shape = tf.image.extract_jpeg_shape(image_bytes)

      # Crops image.
      cropped_image = preprocess_ops.random_crop_image_v2(
          image_bytes, image_shape, area_range=self._crop_area_range)
      image = tf.cond(
          tf.reduce_all(tf.equal(tf.shape(cropped_image), image_shape)),
          lambda: preprocess_ops.center_crop_image_v2(image_bytes, image_shape),
          lambda: cropped_image)
    else:
      if require_decoding:
        # Decodes image.
        image = tf.io.decode_image(image_bytes, channels=3)
        image.set_shape([None, None, 3])
      else:
        # Already decoded image matrix
        image = image_bytes

      # Crops image.
      if self._aug_crop:
        cropped_image = preprocess_ops.random_crop_image(
            image, area_range=self._crop_area_range)

        image = tf.cond(
            tf.reduce_all(tf.equal(tf.shape(cropped_image), tf.shape(image))),
            lambda: preprocess_ops.center_crop_image(image),
            lambda: cropped_image)

    if self._aug_rand_hflip:
      image = tf.image.random_flip_left_right(image)

    # Color jitter.
    if self._color_jitter > 0:
      image = preprocess_ops.color_jitter(image, self._color_jitter,
                                          self._color_jitter,
                                          self._color_jitter)

    # Resizes image.
    image = tf.image.resize(
        image, self._output_size, method=self._tf_resize_method)
    image.set_shape([self._output_size[0], self._output_size[1], 3])

    # Apply autoaug or randaug.
    if self._augmenter is not None:
      image = self._augmenter.distort(image)

    # Three augmentation
    if self._three_augment:
      image = augment.AutoAugment(
          augmentation_name='deit3_three_augment',
          translate_const=20,
      ).distort(image)

    # Normalizes image with mean and std pixel values.
    image = preprocess_ops.normalize_image(
        image, offset=preprocess_ops.MEAN_RGB, scale=preprocess_ops.STDDEV_RGB)

    # Random erasing after the image has been normalized
    if self._random_erasing is not None:
      image = self._random_erasing.distort(image)

    # Convert image to self._dtype.
    image = tf.image.convert_image_dtype(image, self._dtype)

    return image