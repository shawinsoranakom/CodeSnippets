def _parse_train_data(self, data):
    """Parse data for ShapeMask training."""
    classes = data['groundtruth_classes']
    boxes = data['groundtruth_boxes']
    masks = data['groundtruth_instance_masks']
    is_crowds = data['groundtruth_is_crowd']
    # Skips annotations with `is_crowd` = True.
    if self._skip_crowd_during_training and self._is_training:
      num_groundtrtuhs = tf.shape(classes)[0]
      with tf.control_dependencies([num_groundtrtuhs, is_crowds]):
        indices = tf.cond(
            tf.greater(tf.size(is_crowds), 0),
            lambda: tf.where(tf.logical_not(is_crowds))[:, 0],
            lambda: tf.cast(tf.range(num_groundtrtuhs), tf.int64))
      classes = tf.gather(classes, indices)
      boxes = tf.gather(boxes, indices)
      masks = tf.gather(masks, indices)

    # Gets original image and its size.
    image = data['image']
    image_shape = tf.shape(image)[0:2]

    # If not using category, makes all categories with id = 0.
    if not self._use_category:
      classes = tf.cast(tf.greater(classes, 0), dtype=tf.float32)

    # Normalizes image with mean and std pixel values.
    image = input_utils.normalize_image(image)

    # Flips image randomly during training.
    if self._aug_rand_hflip:
      image, boxes, masks = input_utils.random_horizontal_flip(
          image, boxes, masks)

    # Converts boxes from normalized coordinates to pixel coordinates.
    boxes = box_utils.denormalize_boxes(boxes, image_shape)

    # Resizes and crops image.
    image, image_info = input_utils.resize_and_crop_image(
        image,
        self._output_size,
        self._output_size,
        aug_scale_min=self._aug_scale_min,
        aug_scale_max=self._aug_scale_max)
    image_scale = image_info[2, :]
    offset = image_info[3, :]

    # Resizes and crops boxes and masks.
    boxes = input_utils.resize_and_crop_boxes(
        boxes, image_scale, image_info[1, :], offset)

    # Filters out ground truth boxes that are all zeros.
    indices = box_utils.get_non_empty_box_indices(boxes)
    boxes = tf.gather(boxes, indices)
    classes = tf.gather(classes, indices)
    masks = tf.gather(masks, indices)

    # Assigns anchors.
    input_anchor = anchor.Anchor(
        self._min_level, self._max_level, self._num_scales,
        self._aspect_ratios, self._anchor_size, self._output_size)
    anchor_labeler = anchor.AnchorLabeler(
        input_anchor, self._match_threshold, self._unmatched_threshold)
    (cls_targets,
     box_targets,
     num_positives) = anchor_labeler.label_anchors(
         boxes,
         tf.cast(tf.expand_dims(classes, axis=1), tf.float32))

    # Sample groundtruth masks/boxes/classes for mask branch.
    num_masks = tf.shape(masks)[0]
    mask_shape = tf.shape(masks)[1:3]

    # Pad sampled boxes/masks/classes to a constant batch size.
    padded_boxes = pad_to_size(boxes, self._num_sampled_masks)
    padded_classes = pad_to_size(classes, self._num_sampled_masks)
    padded_masks = pad_to_size(masks, self._num_sampled_masks)

    # Randomly sample groundtruth masks for mask branch training. For the image
    # without groundtruth masks, it will sample the dummy padded tensors.
    rand_indices = tf.random.shuffle(
        tf.range(tf.maximum(num_masks, self._num_sampled_masks)))
    rand_indices = tf.math.mod(rand_indices, tf.maximum(num_masks, 1))
    rand_indices = rand_indices[0:self._num_sampled_masks]
    rand_indices = tf.reshape(rand_indices, [self._num_sampled_masks])

    sampled_boxes = tf.gather(padded_boxes, rand_indices)
    sampled_classes = tf.gather(padded_classes, rand_indices)
    sampled_masks = tf.gather(padded_masks, rand_indices)
    # Jitter the sampled boxes to mimic the noisy detections.
    sampled_boxes = box_utils.jitter_boxes(
        sampled_boxes, noise_scale=self._box_jitter_scale)
    sampled_boxes = box_utils.clip_boxes(sampled_boxes, self._output_size)
    # Compute mask targets in feature crop. A feature crop fully contains a
    # sampled box.
    mask_outer_boxes = box_utils.compute_outer_boxes(
        sampled_boxes, tf.shape(image)[0:2], scale=self._outer_box_scale)
    mask_outer_boxes = box_utils.clip_boxes(mask_outer_boxes, self._output_size)
    # Compensate the offset of mask_outer_boxes to map it back to original image
    # scale.
    mask_outer_boxes_ori = mask_outer_boxes
    mask_outer_boxes_ori += tf.tile(tf.expand_dims(offset, axis=0), [1, 2])
    mask_outer_boxes_ori /= tf.tile(tf.expand_dims(image_scale, axis=0), [1, 2])
    norm_mask_outer_boxes_ori = box_utils.normalize_boxes(
        mask_outer_boxes_ori, mask_shape)

    # Set sampled_masks shape to [batch_size, height, width, 1].
    sampled_masks = tf.cast(tf.expand_dims(sampled_masks, axis=-1), tf.float32)
    mask_targets = tf.image.crop_and_resize(
        sampled_masks,
        norm_mask_outer_boxes_ori,
        box_indices=tf.range(self._num_sampled_masks),
        crop_size=[self._mask_crop_size, self._mask_crop_size],
        method='bilinear',
        extrapolation_value=0,
        name='train_mask_targets')
    mask_targets = tf.where(tf.greater_equal(mask_targets, 0.5),
                            tf.ones_like(mask_targets),
                            tf.zeros_like(mask_targets))
    mask_targets = tf.squeeze(mask_targets, axis=-1)
    if self._up_sample_factor > 1:
      fine_mask_targets = tf.image.crop_and_resize(
          sampled_masks,
          norm_mask_outer_boxes_ori,
          box_indices=tf.range(self._num_sampled_masks),
          crop_size=[
              self._mask_crop_size * self._up_sample_factor,
              self._mask_crop_size * self._up_sample_factor
          ],
          method='bilinear',
          extrapolation_value=0,
          name='train_mask_targets')
      fine_mask_targets = tf.where(
          tf.greater_equal(fine_mask_targets, 0.5),
          tf.ones_like(fine_mask_targets), tf.zeros_like(fine_mask_targets))
      fine_mask_targets = tf.squeeze(fine_mask_targets, axis=-1)
    else:
      fine_mask_targets = mask_targets

    # If bfloat16 is used, casts input image to tf.bfloat16.
    if self._use_bfloat16:
      image = tf.cast(image, dtype=tf.bfloat16)

    valid_image = tf.cast(tf.not_equal(num_masks, 0), tf.int32)
    if self._mask_train_class == 'all':
      mask_is_valid = valid_image * tf.ones_like(sampled_classes, tf.int32)
    else:
      # Get the intersection of sampled classes with training splits.
      mask_valid_classes = tf.cast(
          tf.expand_dims(
              class_utils.coco_split_class_ids(self._mask_train_class), 1),
          sampled_classes.dtype)
      match = tf.reduce_any(
          tf.equal(tf.expand_dims(sampled_classes, 0), mask_valid_classes), 0)
      mask_is_valid = valid_image * tf.cast(match, tf.int32)

    # Packs labels for model_fn outputs.
    labels = {
        'cls_targets': cls_targets,
        'box_targets': box_targets,
        'anchor_boxes': input_anchor.multilevel_boxes,
        'num_positives': num_positives,
        'image_info': image_info,
        # For ShapeMask.
        'mask_targets': mask_targets,
        'fine_mask_targets': fine_mask_targets,
        'mask_is_valid': mask_is_valid,
    }

    inputs = {
        'image': image,
        'image_info': image_info,
        'mask_boxes': sampled_boxes,
        'mask_outer_boxes': mask_outer_boxes,
        'mask_classes': sampled_classes,
    }
    return inputs, labels