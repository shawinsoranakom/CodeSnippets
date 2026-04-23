def random_crop_to_aspect_ratio(image,
                                boxes,
                                labels,
                                label_weights,
                                label_confidences=None,
                                multiclass_scores=None,
                                masks=None,
                                keypoints=None,
                                aspect_ratio=1.0,
                                overlap_thresh=0.3,
                                clip_boxes=True,
                                center_crop=False,
                                seed=None,
                                preprocess_vars_cache=None):
  """Randomly crops an image to the specified aspect ratio.

  Randomly crops the a portion of the image such that the crop is of the
  specified aspect ratio, and the crop is as large as possible. If the specified
  aspect ratio is larger than the aspect ratio of the image, this op will
  randomly remove rows from the top and bottom of the image. If the specified
  aspect ratio is less than the aspect ratio of the image, this op will randomly
  remove cols from the left and right of the image. If the specified aspect
  ratio is the same as the aspect ratio of the image, this op will return the
  image.

  Args:
    image: rank 3 float32 tensor contains 1 image -> [height, width, channels]
           with pixel values varying between [0, 1].
    boxes: rank 2 float32 tensor containing the bounding boxes -> [N, 4].
           Boxes are in normalized form meaning their coordinates vary
           between [0, 1].
           Each row is in the form of [ymin, xmin, ymax, xmax].
    labels: rank 1 int32 tensor containing the object classes.
    label_weights: float32 tensor of shape [num_instances] representing the
      weight for each box.
    label_confidences: (optional) float32 tensor of shape [num_instances]
      representing the confidence for each box.
    multiclass_scores: (optional) float32 tensor of shape
      [num_instances, num_classes] representing the score for each box for each
      class.
    masks: (optional) rank 3 float32 tensor with shape
           [num_instances, height, width] containing instance masks. The masks
           are of the same height, width as the input `image`.
    keypoints: (optional) rank 3 float32 tensor with shape
               [num_instances, num_keypoints, 2]. The keypoints are in y-x
               normalized coordinates.
    aspect_ratio: the aspect ratio of cropped image.
    overlap_thresh: minimum overlap thresh with new cropped
                    image to keep the box.
    clip_boxes: whether to clip the boxes to the cropped image.
    center_crop: whether to take the center crop or a random crop.
    seed: random seed.
    preprocess_vars_cache: PreprocessorCache object that records previously
                           performed augmentations. Updated in-place. If this
                           function is called multiple times with the same
                           non-null cache, it will perform deterministically.

  Returns:
    image: image which is the same rank as input image.
    boxes: boxes which is the same rank as input boxes.
           Boxes are in normalized form.
    labels: new labels.

    If label_weights, masks, keypoints, or multiclass_scores is not None, the
    function also returns:
    label_weights: rank 1 float32 tensor with shape [num_instances].
    masks: rank 3 float32 tensor with shape [num_instances, height, width]
           containing instance masks.
    keypoints: rank 3 float32 tensor with shape
               [num_instances, num_keypoints, 2]
    multiclass_scores: rank 2 float32 tensor with shape
                       [num_instances, num_classes]

  Raises:
    ValueError: If image is not a 3D tensor.
  """
  if len(image.get_shape()) != 3:
    raise ValueError('Image should be 3D tensor')

  with tf.name_scope('RandomCropToAspectRatio', values=[image]):
    image_shape = tf.shape(image)
    orig_height = image_shape[0]
    orig_width = image_shape[1]
    orig_aspect_ratio = tf.cast(
        orig_width, dtype=tf.float32) / tf.cast(
            orig_height, dtype=tf.float32)
    new_aspect_ratio = tf.constant(aspect_ratio, dtype=tf.float32)

    def target_height_fn():
      return tf.cast(
          tf.round(tf.cast(orig_width, dtype=tf.float32) / new_aspect_ratio),
          dtype=tf.int32)

    target_height = tf.cond(orig_aspect_ratio >= new_aspect_ratio,
                            lambda: orig_height, target_height_fn)

    def target_width_fn():
      return tf.cast(
          tf.round(tf.cast(orig_height, dtype=tf.float32) * new_aspect_ratio),
          dtype=tf.int32)

    target_width = tf.cond(orig_aspect_ratio <= new_aspect_ratio,
                           lambda: orig_width, target_width_fn)

    # either offset_height = 0 and offset_width is randomly chosen from
    # [0, offset_width - target_width), or else offset_width = 0 and
    # offset_height is randomly chosen from [0, offset_height - target_height)
    if center_crop:
      offset_height = tf.cast(tf.math.floor((orig_height - target_height) / 2),
                              tf.int32)
      offset_width = tf.cast(tf.math.floor((orig_width - target_width) / 2),
                             tf.int32)
    else:
      offset_height = _random_integer(0, orig_height - target_height + 1, seed)
      offset_width = _random_integer(0, orig_width - target_width + 1, seed)

    generator_func = lambda: (offset_height, offset_width)
    offset_height, offset_width = _get_or_create_preprocess_rand_vars(
        generator_func,
        preprocessor_cache.PreprocessorCache.CROP_TO_ASPECT_RATIO,
        preprocess_vars_cache)

    new_image = tf.image.crop_to_bounding_box(
        image, offset_height, offset_width, target_height, target_width)

    im_box = tf.stack([
        tf.cast(offset_height, dtype=tf.float32) /
        tf.cast(orig_height, dtype=tf.float32),
        tf.cast(offset_width, dtype=tf.float32) /
        tf.cast(orig_width, dtype=tf.float32),
        tf.cast(offset_height + target_height, dtype=tf.float32) /
        tf.cast(orig_height, dtype=tf.float32),
        tf.cast(offset_width + target_width, dtype=tf.float32) /
        tf.cast(orig_width, dtype=tf.float32)
    ])

    boxlist = box_list.BoxList(boxes)
    boxlist.add_field('labels', labels)

    boxlist.add_field('label_weights', label_weights)

    if label_confidences is not None:
      boxlist.add_field('label_confidences', label_confidences)

    if multiclass_scores is not None:
      boxlist.add_field('multiclass_scores', multiclass_scores)

    im_boxlist = box_list.BoxList(tf.expand_dims(im_box, 0))

    # remove boxes whose overlap with the image is less than overlap_thresh
    overlapping_boxlist, keep_ids = box_list_ops.prune_non_overlapping_boxes(
        boxlist, im_boxlist, overlap_thresh)

    # change the coordinate of the remaining boxes
    new_labels = overlapping_boxlist.get_field('labels')
    new_boxlist = box_list_ops.change_coordinate_frame(overlapping_boxlist,
                                                       im_box)
    if clip_boxes:
      new_boxlist = box_list_ops.clip_to_window(
          new_boxlist, tf.constant([0.0, 0.0, 1.0, 1.0], tf.float32))
    new_boxes = new_boxlist.get()

    result = [new_image, new_boxes, new_labels]

    new_label_weights = overlapping_boxlist.get_field('label_weights')
    result.append(new_label_weights)

    if label_confidences is not None:
      new_label_confidences = (
          overlapping_boxlist.get_field('label_confidences'))
      result.append(new_label_confidences)

    if multiclass_scores is not None:
      new_multiclass_scores = overlapping_boxlist.get_field('multiclass_scores')
      result.append(new_multiclass_scores)

    if masks is not None:
      masks_inside_window = tf.gather(masks, keep_ids)
      masks_box_begin = tf.stack([0, offset_height, offset_width])
      masks_box_size = tf.stack([-1, target_height, target_width])
      new_masks = tf.slice(masks_inside_window, masks_box_begin, masks_box_size)
      result.append(new_masks)

    if keypoints is not None:
      keypoints_inside_window = tf.gather(keypoints, keep_ids)
      new_keypoints = keypoint_ops.change_coordinate_frame(
          keypoints_inside_window, im_box)
      if clip_boxes:
        new_keypoints = keypoint_ops.prune_outside_window(new_keypoints,
                                                          [0.0, 0.0, 1.0, 1.0])
      result.append(new_keypoints)

    return tuple(result)