def _parse_train_data(self, data, anchor_labeler=None, input_anchor=None):
    """Parses data for training and evaluation."""
    classes = data['groundtruth_classes']
    boxes = data['groundtruth_boxes']
    # If not empty, `attributes` is a dict of (name, ground_truth) pairs.
    # `ground_truth` of attributes is assumed in shape [N, attribute_size].
    attributes = data.get('groundtruth_attributes', {})
    is_crowds = data['groundtruth_is_crowd']

    # Skips annotations with `is_crowd` = True.
    if self._skip_crowd_during_training:
      num_groundtruths = tf.shape(input=classes)[0]
      with tf.control_dependencies([num_groundtruths, is_crowds]):
        indices = tf.cond(
            pred=tf.greater(tf.size(input=is_crowds), 0),
            true_fn=lambda: tf.where(tf.logical_not(is_crowds))[:, 0],
            false_fn=lambda: tf.cast(tf.range(num_groundtruths), tf.int64))
      classes = tf.gather(classes, indices)
      boxes = tf.gather(boxes, indices)
      for k, v in attributes.items():
        attributes[k] = tf.gather(v, indices)

    # Gets original image.
    image = data['image']
    image_size = tf.cast(tf.shape(image)[0:2], tf.float32)

    less_output_pixels = (
        self._output_size[0] * self._output_size[1]
    ) < image_size[0] * image_size[1]

    # Resizing first can reduce augmentation computation if the original image
    # has more pixels than the desired output image.
    # There might be a smarter threshold to compute less_output_pixels as
    # we keep the padding to the very end, i.e., a resized image likely has less
    # pixels than self._output_size[0] * self._output_size[1].
    resize_first = self._resize_first and less_output_pixels
    if resize_first:
      image, boxes, image_info = self._resize_and_crop_image_and_boxes(
          image, boxes, pad=False
      )
      image = tf.cast(image, dtype=tf.uint8)

    # Apply autoaug or randaug.
    if self._augmenter is not None:
      image, boxes = self._augmenter.distort_with_boxes(image, boxes)

    # Apply random jpeg quality change.
    if self._aug_rand_jpeg is not None:
      image = preprocess_ops.random_jpeg_quality(
          image,
          min_quality=self._aug_rand_jpeg.min_quality,
          max_quality=self._aug_rand_jpeg.max_quality,
          prob_to_apply=self._aug_rand_jpeg.prob_to_apply,
      )

    image_shape = tf.shape(input=image)[0:2]

    # Normalizes image with mean and std pixel values.
    image = preprocess_ops.normalize_image(image)

    # Flips image randomly during training.
    if self._aug_rand_hflip:
      image, boxes, _ = preprocess_ops.random_horizontal_flip(image, boxes)

    # Converts boxes from normalized coordinates to pixel coordinates.
    boxes = box_ops.denormalize_boxes(boxes, image_shape)

    if self._pad:
      padded_size = preprocess_ops.compute_padded_size(
          self._output_size, 2**self._max_level
      )
    else:
      padded_size = self._output_size

    if not resize_first:
      image, boxes, image_info = (
          self._resize_and_crop_image_and_boxes(image, boxes, pad=self._pad)
      )

    image = tf.image.pad_to_bounding_box(
        image, 0, 0, padded_size[0], padded_size[1]
    )
    image = tf.ensure_shape(image, padded_size + [3])

    image_height, image_width, _ = image.get_shape().as_list()

    # Filters out ground-truth boxes that are all zeros.
    indices = box_ops.get_non_empty_box_indices(boxes)
    boxes = tf.gather(boxes, indices)
    classes = tf.gather(classes, indices)
    for k, v in attributes.items():
      attributes[k] = tf.gather(v, indices)

    # Assigns anchors.
    if input_anchor is None:
      input_anchor = anchor.build_anchor_generator(
          min_level=self._min_level,
          max_level=self._max_level,
          num_scales=self._num_scales,
          aspect_ratios=self._aspect_ratios,
          anchor_size=self._anchor_size,
      )

    anchor_boxes = input_anchor(image_size=(image_height, image_width))
    if anchor_labeler is None:
      anchor_labeler = anchor.AnchorLabeler(
          match_threshold=self._match_threshold,
          unmatched_threshold=self._unmatched_threshold,
          box_coder_weights=self._box_coder_weights,
      )
    (cls_targets, box_targets, att_targets, cls_weights,
     box_weights) = anchor_labeler.label_anchors(
         anchor_boxes, boxes, tf.expand_dims(classes, axis=1), attributes)

    # Casts input image to desired data type.
    image = tf.cast(image, dtype=self._dtype)

    # Packs labels for model_fn outputs.
    labels = {
        'cls_targets': cls_targets,
        'box_targets': box_targets,
        'anchor_boxes': anchor_boxes,
        'cls_weights': cls_weights,
        'box_weights': box_weights,
        'image_info': image_info,
    }
    if att_targets:
      labels['attribute_targets'] = att_targets
    return image, labels