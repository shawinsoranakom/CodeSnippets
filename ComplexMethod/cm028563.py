def _parse_train_data(self, data):
    """Generates images and labels that are usable for model training.

    We use random flip, random scaling (between 0.6 to 1.3), cropping,
    and color jittering as data augmentation

    Args:
        data: the decoded tensor dictionary from TfExampleDecoder.

    Returns:
        images: the image tensor.
        labels: a dict of Tensors that contains labels.
    """

    image = tf.cast(data['image'], dtype=tf.float32)
    boxes = data['groundtruth_boxes']
    classes = data['groundtruth_classes']

    image_shape = tf.shape(input=image)[0:2]

    if self._aug_rand_hflip:
      image, boxes, _ = preprocess_ops.random_horizontal_flip(image, boxes)

    # Image augmentation
    if not self._odapi_augmentation:
      # Color and lighting jittering
      if self._aug_rand_hue:
        image = tf.image.random_hue(
            image=image, max_delta=.02)
      if self._aug_rand_contrast:
        image = tf.image.random_contrast(
            image=image, lower=0.8, upper=1.25)
      if self._aug_rand_saturation:
        image = tf.image.random_saturation(
            image=image, lower=0.8, upper=1.25)
      if self._aug_rand_brightness:
        image = tf.image.random_brightness(
            image=image, max_delta=.2)
      image = tf.clip_by_value(image, clip_value_min=0.0, clip_value_max=255.0)
      # Converts boxes from normalized coordinates to pixel coordinates.
      boxes = box_ops.denormalize_boxes(boxes, image_shape)

      # Resizes and crops image.
      image, image_info = preprocess_ops.resize_and_crop_image(
          image,
          [self._output_height, self._output_width],
          padded_size=[self._output_height, self._output_width],
          aug_scale_min=self._aug_scale_min,
          aug_scale_max=self._aug_scale_max)
      unpad_image_shape = tf.cast(tf.shape(image), tf.float32)

      # Resizes and crops boxes.
      image_scale = image_info[2, :]
      offset = image_info[3, :]
      boxes = preprocess_ops.resize_and_crop_boxes(boxes, image_scale,
                                                   image_info[1, :], offset)

    else:
      # Color and lighting jittering
      if self._aug_rand_hue:
        image = cn_prep_ops.random_adjust_hue(
            image=image, max_delta=.02)
      if self._aug_rand_contrast:
        image = cn_prep_ops.random_adjust_contrast(
            image=image, min_delta=0.8, max_delta=1.25)
      if self._aug_rand_saturation:
        image = cn_prep_ops.random_adjust_saturation(
            image=image, min_delta=0.8, max_delta=1.25)
      if self._aug_rand_brightness:
        image = cn_prep_ops.random_adjust_brightness(
            image=image, max_delta=.2)

      sc_image, sc_boxes, classes = cn_prep_ops.random_square_crop_by_scale(
          image=image,
          boxes=boxes,
          labels=classes,
          scale_min=self._aug_scale_min,
          scale_max=self._aug_scale_max)

      image, unpad_image_shape = cn_prep_ops.resize_to_range(
          image=sc_image,
          min_dimension=self._output_width,
          max_dimension=self._output_width,
          pad_to_max_dimension=True)
      preprocessed_shape = tf.cast(tf.shape(image), tf.float32)
      unpad_image_shape = tf.cast(unpad_image_shape, tf.float32)

      im_box = tf.stack([
          0.0,
          0.0,
          preprocessed_shape[0] / unpad_image_shape[0],
          preprocessed_shape[1] / unpad_image_shape[1]
      ])
      realigned_bboxes = box_list_ops.change_coordinate_frame(
          boxlist=box_list.BoxList(sc_boxes),
          window=im_box)

      valid_boxes = box_list_ops.assert_or_prune_invalid_boxes(
          realigned_bboxes.get())

      boxes = box_list_ops.to_absolute_coordinates(
          boxlist=box_list.BoxList(valid_boxes),
          height=self._output_height,
          width=self._output_width).get()

      image_info = tf.stack([
          tf.cast(image_shape, dtype=tf.float32),
          tf.constant([self._output_height, self._output_width],
                      dtype=tf.float32),
          tf.cast(tf.shape(sc_image)[0:2] / image_shape, dtype=tf.float32),
          tf.constant([0., 0.])
      ])

    # Filters out ground truth boxes that are all zeros.
    indices = box_ops.get_non_empty_box_indices(boxes)
    boxes = tf.gather(boxes, indices)
    classes = tf.gather(classes, indices)

    labels = self._build_label(
        unpad_image_shape=unpad_image_shape,
        boxes=boxes,
        classes=classes,
        image_info=image_info,
        data=data)

    if self._bgr_ordering:
      red, green, blue = tf.unstack(image, num=3, axis=2)
      image = tf.stack([blue, green, red], axis=2)

    image = preprocess_ops.normalize_image(
        image=image,
        offset=self._channel_means,
        scale=self._channel_stds)

    image = tf.cast(image, self._dtype)

    return image, labels