def _parse_train_data(self, data):
    """Parses data for training.

    Args:
      data: the decoded tensor dictionary from TfExampleDecoder.

    Returns:
      image: image tensor that is preproessed to have normalized value and
        dimension [output_size[0], output_size[1], 3]
      labels: a dictionary of tensors used for training. The following describes
        {key: value} pairs in the dictionary.
        image_info: a 2D `Tensor` that encodes the information of the image and
          the applied preprocessing. It is in the format of
          [[original_height, original_width], [scaled_height, scaled_width],
        anchor_boxes: ordered dictionary with keys
          [min_level, min_level+1, ..., max_level]. The values are tensor with
          shape [height_l, width_l, 4] representing anchor boxes at each level.
        rpn_score_targets: ordered dictionary with keys
          [min_level, min_level+1, ..., max_level]. The values are tensor with
          shape [height_l, width_l, anchors_per_location]. The height_l and
          width_l represent the dimension of class logits at l-th level.
        rpn_box_targets: ordered dictionary with keys
          [min_level, min_level+1, ..., max_level]. The values are tensor with
          shape [height_l, width_l, anchors_per_location * 4]. The height_l and
          width_l represent the dimension of bounding box regression output at
          l-th level.
        gt_boxes: Ground-truth bounding box annotations. The box is represented
           in [y1, x1, y2, x2] format. The coordinates are w.r.t the scaled
           image that is fed to the network. The tennsor is padded with -1 to
           the fixed dimension [self._max_num_instances, 4].
        gt_classes: Ground-truth classes annotations. The tennsor is padded
          with -1 to the fixed dimension [self._max_num_instances].
        gt_masks: groundtrugh masks cropped by the bounding box and
          resized to a fixed size determined by mask_crop_size.
    """
    classes = data['groundtruth_classes']
    boxes = data['groundtruth_boxes']
    if self._include_mask:
      masks = data['groundtruth_instance_masks']

    is_crowds = data['groundtruth_is_crowd']
    # Skips annotations with `is_crowd` = True.
    if self._skip_crowd_during_training:
      num_groundtruths = tf.shape(classes)[0]
      with tf.control_dependencies([num_groundtruths, is_crowds]):
        indices = tf.cond(
            tf.greater(tf.size(is_crowds), 0),
            lambda: tf.where(tf.logical_not(is_crowds))[:, 0],
            lambda: tf.cast(tf.range(num_groundtruths), tf.int64))
      classes = tf.gather(classes, indices)
      boxes = tf.gather(boxes, indices)
      if self._include_mask:
        masks = tf.gather(masks, indices)

    # Gets original image and its size.
    image = data['image']
    if self._augmenter is not None:
      image = self._augmenter.distort(image)

    image_shape = tf.shape(image)[0:2]

    # Normalizes image with mean and std pixel values.
    image = preprocess_ops.normalize_image(image)

    # Flips image randomly during training.
    image, boxes, masks = preprocess_ops.random_horizontal_flip(
        image,
        boxes,
        masks=None if not self._include_mask else masks,
        prob=tf.where(self._aug_rand_hflip, 0.5, 0.0),
    )
    image, boxes, masks = preprocess_ops.random_vertical_flip(
        image,
        boxes,
        masks=None if not self._include_mask else masks,
        prob=tf.where(self._aug_rand_vflip, 0.5, 0.0),
    )

    # Converts boxes from normalized coordinates to pixel coordinates.
    # Now the coordinates of boxes are w.r.t. the original image.
    boxes = box_ops.denormalize_boxes(boxes, image_shape)

    # Resizes and crops image.
    image, image_info = preprocess_ops.resize_and_crop_image(
        image,
        self._output_size,
        padded_size=preprocess_ops.compute_padded_size(
            self._output_size, 2 ** self._max_level),
        aug_scale_min=self._aug_scale_min,
        aug_scale_max=self._aug_scale_max)
    image_height, image_width, _ = image.get_shape().as_list()

    # Resizes and crops boxes.
    # Now the coordinates of boxes are w.r.t the scaled image.
    image_scale = image_info[2, :]
    offset = image_info[3, :]
    boxes = preprocess_ops.resize_and_crop_boxes(
        boxes, image_scale, image_info[1, :], offset)

    # Filters out ground-truth boxes that are all zeros.
    indices = box_ops.get_non_empty_box_indices(boxes)
    boxes = tf.gather(boxes, indices)
    classes = tf.gather(classes, indices)
    if self._include_mask:
      outer_boxes = box_ops.compute_outer_boxes(boxes, image_info[1, :],
                                                self._outer_boxes_scale)
      masks = tf.gather(masks, indices)
      # Transfer boxes to the original image space and do normalization.
      cropped_boxes = outer_boxes + tf.tile(
          tf.expand_dims(offset, axis=0), [1, 2])
      cropped_boxes /= tf.tile(tf.expand_dims(image_scale, axis=0), [1, 2])
      cropped_boxes = box_ops.normalize_boxes(cropped_boxes, image_shape)
      num_masks = tf.shape(masks)[0]
      masks = tf.image.crop_and_resize(
          tf.expand_dims(masks, axis=-1),
          cropped_boxes,
          box_indices=tf.range(num_masks, dtype=tf.int32),
          crop_size=[self._mask_crop_size, self._mask_crop_size],
          method='bilinear')
      masks = tf.squeeze(masks, axis=-1)

    # Assigns anchor targets.
    # Note that after the target assignment, box targets are absolute pixel
    # offsets w.r.t. the scaled image.
    input_anchor = anchor.build_anchor_generator(
        min_level=self._min_level,
        max_level=self._max_level,
        num_scales=self._num_scales,
        aspect_ratios=self._aspect_ratios,
        anchor_size=self._anchor_size)
    anchor_boxes = input_anchor(image_size=(image_height, image_width))
    anchor_labeler = anchor.RpnAnchorLabeler(
        self._rpn_match_threshold,
        self._rpn_unmatched_threshold,
        self._rpn_batch_size_per_im,
        self._rpn_fg_fraction)
    rpn_score_targets, rpn_box_targets = anchor_labeler.label_anchors(
        anchor_boxes, boxes,
        tf.cast(tf.expand_dims(classes, axis=-1), dtype=tf.float32))

    # Casts input image to self._dtype
    image = tf.cast(image, dtype=self._dtype)
    boxes = preprocess_ops.clip_or_pad_to_fixed_size(
        boxes, self._max_num_instances, -1)
    classes = preprocess_ops.clip_or_pad_to_fixed_size(
        classes, self._max_num_instances, -1)

    # Packs labels for model_fn outputs.
    labels = {
        'anchor_boxes': anchor_boxes,
        'image_info': image_info,
        'rpn_score_targets': rpn_score_targets,
        'rpn_box_targets': rpn_box_targets,
        'gt_boxes': boxes,
        'gt_classes': classes,
    }
    if self._include_mask:
      outer_boxes = preprocess_ops.clip_or_pad_to_fixed_size(
          outer_boxes, self._max_num_instances, -1)
      masks = preprocess_ops.clip_or_pad_to_fixed_size(
          masks, self._max_num_instances, -1)
      labels.update({
          'gt_outer_boxes': outer_boxes,
          'gt_masks': masks,
      })

    return image, labels