def _prepare_image_and_label(self, data):
    """Prepare normalized image and label."""
    height = data['image/height']
    width = data['image/width']

    label = tf.io.decode_image(
        data['image/segmentation/class/encoded'], channels=1
    )
    label = tf.reshape(label, (1, height, width))
    label = tf.cast(label, tf.float32)

    image = tf.io.decode_image(
        data[self._image_feature.feature_name],
        channels=self._image_feature.num_channels,
        dtype=tf.uint8,
    )
    image = tf.reshape(image, (height, width, self._image_feature.num_channels))
    # Normalizes the image feature.
    # The mean and stddev values are divided by 255 to ensure correct
    # normalization, as the input `uint8` image is automatically converted to
    # `float32` and rescaled to values in the range [0, 1] before the
    # normalization happens (as a pre-processing step). So, we re-scale the
    # mean and stddev values to the range [0, 1] beforehand.
    # See `preprocess_ops.normalize_image` for details on the expected ranges
    # for the image mean (`offset`) and stddev (`scale`).
    image = preprocess_ops.normalize_image(
        image,
        [mean / 255.0 for mean in self._image_feature.mean],
        [stddev / 255.0 for stddev in self._image_feature.stddev],
    )

    if self._additional_dense_features:
      input_list = [image]
      for feature_cfg in self._additional_dense_features:
        feature = tf.io.decode_image(
            data[feature_cfg.feature_name],
            channels=feature_cfg.num_channels,
            dtype=tf.uint8,
        )
        feature = tf.reshape(feature, (height, width, feature_cfg.num_channels))
        feature = preprocess_ops.normalize_image(
            feature,
            [mean / 255.0 for mean in feature_cfg.mean],
            [stddev / 255.0 for stddev in feature_cfg.stddev],
        )
        input_list.append(feature)
      concat_input = tf.concat(input_list, axis=2)
    else:
      concat_input = image

    if not self._preserve_aspect_ratio:
      label = tf.reshape(label, [data['image/height'], data['image/width'], 1])
      concat_input = tf.image.resize(
          concat_input, self._output_size, method='bilinear'
      )
      label = tf.image.resize(label, self._output_size, method='nearest')
      label = tf.reshape(label[:, :, -1], [1] + self._output_size)

    return concat_input, label