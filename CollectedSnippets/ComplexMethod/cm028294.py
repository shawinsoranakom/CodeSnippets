def _strict_random_crop_image(image,
                              boxes,
                              labels,
                              label_weights,
                              label_confidences=None,
                              multiclass_scores=None,
                              masks=None,
                              mask_weights=None,
                              keypoints=None,
                              keypoint_visibilities=None,
                              densepose_num_points=None,
                              densepose_part_ids=None,
                              densepose_surface_coords=None,
                              min_object_covered=1.0,
                              aspect_ratio_range=(0.75, 1.33),
                              area_range=(0.1, 1.0),
                              overlap_thresh=0.3,
                              clip_boxes=True,
                              preprocess_vars_cache=None):
  """Performs random crop.

  Note: Keypoint coordinates that are outside the crop will be set to NaN, which
  is consistent with the original keypoint encoding for non-existing keypoints.
  This function always crops the image and is supposed to be used by
  `random_crop_image` function which sometimes returns the image unchanged.

  Args:
    image: rank 3 float32 tensor containing 1 image -> [height, width, channels]
           with pixel values varying between [0, 1].
    boxes: rank 2 float32 tensor containing the bounding boxes with shape
           [num_instances, 4].
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
    mask_weights: (optional) rank 1 float32 tensor with shape [num_instances]
                  with instance masks weights.
    keypoints: (optional) rank 3 float32 tensor with shape
               [num_instances, num_keypoints, 2]. The keypoints are in y-x
               normalized coordinates.
    keypoint_visibilities: (optional) rank 2 bool tensor with shape
               [num_instances, num_keypoints].
    densepose_num_points: (optional) rank 1 int32 tensor with shape
                          [num_instances] with the number of sampled points per
                          instance.
    densepose_part_ids: (optional) rank 2 int32 tensor with shape
                        [num_instances, num_points] holding the part id for each
                        sampled point. These part_ids are 0-indexed, where the
                        first non-background part has index 0.
    densepose_surface_coords: (optional) rank 3 float32 tensor with shape
                              [num_instances, num_points, 4]. The DensePose
                              coordinates are of the form (y, x, v, u) where
                              (y, x) are the normalized image coordinates for a
                              sampled point, and (v, u) is the surface
                              coordinate for the part.
    min_object_covered: the cropped image must cover at least this fraction of
                        at least one of the input bounding boxes.
    aspect_ratio_range: allowed range for aspect ratio of cropped image.
    area_range: allowed range for area ratio between cropped image and the
                original image.
    overlap_thresh: minimum overlap thresh with new cropped
                    image to keep the box.
    clip_boxes: whether to clip the boxes to the cropped image.
    preprocess_vars_cache: PreprocessorCache object that records previously
                           performed augmentations. Updated in-place. If this
                           function is called multiple times with the same
                           non-null cache, it will perform deterministically.

  Returns:
    image: image which is the same rank as input image.
    boxes: boxes which is the same rank as input boxes.
           Boxes are in normalized form.
    labels: new labels.

    If label_weights, multiclass_scores, masks, mask_weights, keypoints,
    keypoint_visibilities, densepose_num_points, densepose_part_ids, or
    densepose_surface_coords is not None, the function also returns:
    label_weights: rank 1 float32 tensor with shape [num_instances].
    multiclass_scores: rank 2 float32 tensor with shape
                       [num_instances, num_classes]
    masks: rank 3 float32 tensor with shape [num_instances, height, width]
           containing instance masks.
    mask_weights: rank 1 float32 tensor with shape [num_instances] with mask
                  weights.
    keypoints: rank 3 float32 tensor with shape
               [num_instances, num_keypoints, 2]
    keypoint_visibilities: rank 2 bool tensor with shape
                           [num_instances, num_keypoints]
    densepose_num_points: rank 1 int32 tensor with shape [num_instances].
    densepose_part_ids: rank 2 int32 tensor with shape
                        [num_instances, num_points].
    densepose_surface_coords: rank 3 float32 tensor with shape
                              [num_instances, num_points, 4].

  Raises:
    ValueError: If some but not all of the DensePose tensors are provided.
  """
  with tf.name_scope('RandomCropImage', values=[image, boxes]):
    densepose_tensors = [densepose_num_points, densepose_part_ids,
                         densepose_surface_coords]
    if (any(t is not None for t in densepose_tensors) and
        not all(t is not None for t in densepose_tensors)):
      raise ValueError('If cropping DensePose labels, must provide '
                       '`densepose_num_points`, `densepose_part_ids`, and '
                       '`densepose_surface_coords`')
    image_shape = tf.shape(image)

    # boxes are [N, 4]. Lets first make them [N, 1, 4].
    boxes_expanded = tf.expand_dims(
        tf.clip_by_value(
            boxes, clip_value_min=0.0, clip_value_max=1.0), 1)

    generator_func = functools.partial(
        tf.image.sample_distorted_bounding_box,
        image_shape,
        bounding_boxes=boxes_expanded,
        min_object_covered=min_object_covered,
        aspect_ratio_range=aspect_ratio_range,
        area_range=area_range,
        max_attempts=100,
        use_image_if_no_bounding_boxes=True)

    # for ssd cropping, each value of min_object_covered has its own
    # cached random variable
    sample_distorted_bounding_box = _get_or_create_preprocess_rand_vars(
        generator_func,
        preprocessor_cache.PreprocessorCache.STRICT_CROP_IMAGE,
        preprocess_vars_cache, key=min_object_covered)

    im_box_begin, im_box_size, im_box = sample_distorted_bounding_box
    im_box_end = im_box_begin + im_box_size
    new_image = image[im_box_begin[0]:im_box_end[0],
                      im_box_begin[1]:im_box_end[1], :]
    new_image.set_shape([None, None, image.get_shape()[2]])

    # [1, 4]
    im_box_rank2 = tf.squeeze(im_box, axis=[0])
    # [4]
    im_box_rank1 = tf.squeeze(im_box)

    boxlist = box_list.BoxList(boxes)
    boxlist.add_field('labels', labels)

    if label_weights is not None:
      boxlist.add_field('label_weights', label_weights)

    if label_confidences is not None:
      boxlist.add_field('label_confidences', label_confidences)

    if multiclass_scores is not None:
      boxlist.add_field('multiclass_scores', multiclass_scores)

    im_boxlist = box_list.BoxList(im_box_rank2)

    # remove boxes that are outside cropped image
    boxlist, inside_window_ids = box_list_ops.prune_completely_outside_window(
        boxlist, im_box_rank1)

    # remove boxes that are outside image
    overlapping_boxlist, keep_ids = box_list_ops.prune_non_overlapping_boxes(
        boxlist, im_boxlist, overlap_thresh)

    # change the coordinate of the remaining boxes
    new_labels = overlapping_boxlist.get_field('labels')
    new_boxlist = box_list_ops.change_coordinate_frame(overlapping_boxlist,
                                                       im_box_rank1)
    new_boxes = new_boxlist.get()
    if clip_boxes:
      new_boxes = tf.clip_by_value(
          new_boxes, clip_value_min=0.0, clip_value_max=1.0)

    result = [new_image, new_boxes, new_labels]

    if label_weights is not None:
      new_label_weights = overlapping_boxlist.get_field('label_weights')
      result.append(new_label_weights)

    if label_confidences is not None:
      new_label_confidences = overlapping_boxlist.get_field('label_confidences')
      result.append(new_label_confidences)

    if multiclass_scores is not None:
      new_multiclass_scores = overlapping_boxlist.get_field('multiclass_scores')
      result.append(new_multiclass_scores)

    if masks is not None:
      masks_of_boxes_inside_window = tf.gather(masks, inside_window_ids)
      masks_of_boxes_completely_inside_window = tf.gather(
          masks_of_boxes_inside_window, keep_ids)
      new_masks = masks_of_boxes_completely_inside_window[:, im_box_begin[
          0]:im_box_end[0], im_box_begin[1]:im_box_end[1]]
      result.append(new_masks)

    if mask_weights is not None:
      mask_weights_inside_window = tf.gather(mask_weights, inside_window_ids)
      mask_weights_completely_inside_window = tf.gather(
          mask_weights_inside_window, keep_ids)
      result.append(mask_weights_completely_inside_window)

    if keypoints is not None:
      keypoints_of_boxes_inside_window = tf.gather(keypoints, inside_window_ids)
      keypoints_of_boxes_completely_inside_window = tf.gather(
          keypoints_of_boxes_inside_window, keep_ids)
      new_keypoints = keypoint_ops.change_coordinate_frame(
          keypoints_of_boxes_completely_inside_window, im_box_rank1)
      if clip_boxes:
        new_keypoints = keypoint_ops.prune_outside_window(new_keypoints,
                                                          [0.0, 0.0, 1.0, 1.0])
      result.append(new_keypoints)

    if keypoint_visibilities is not None:
      kpt_vis_of_boxes_inside_window = tf.gather(keypoint_visibilities,
                                                 inside_window_ids)
      kpt_vis_of_boxes_completely_inside_window = tf.gather(
          kpt_vis_of_boxes_inside_window, keep_ids)
      if clip_boxes:
        # Set any keypoints with NaN coordinates to invisible.
        new_kpt_visibilities = keypoint_ops.set_keypoint_visibilities(
            new_keypoints, kpt_vis_of_boxes_completely_inside_window)
        result.append(new_kpt_visibilities)

    if densepose_num_points is not None:
      filtered_dp_tensors = []
      for dp_tensor in densepose_tensors:
        dp_tensor_inside_window = tf.gather(dp_tensor, inside_window_ids)
        dp_tensor_completely_inside_window = tf.gather(dp_tensor_inside_window,
                                                       keep_ids)
        filtered_dp_tensors.append(dp_tensor_completely_inside_window)
      new_dp_num_points = filtered_dp_tensors[0]
      new_dp_point_ids = filtered_dp_tensors[1]
      new_dp_surf_coords = densepose_ops.change_coordinate_frame(
          filtered_dp_tensors[2], im_box_rank1)
      if clip_boxes:
        new_dp_num_points, new_dp_point_ids, new_dp_surf_coords = (
            densepose_ops.prune_outside_window(
                new_dp_num_points, new_dp_point_ids, new_dp_surf_coords,
                window=[0.0, 0.0, 1.0, 1.0]))
      result.extend([new_dp_num_points, new_dp_point_ids, new_dp_surf_coords])
    return tuple(result)