def random_crop_image(image,
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
                      random_coef=0.0,
                      seed=None,
                      preprocess_vars_cache=None):
  """Randomly crops the image.

  Given the input image and its bounding boxes, this op randomly
  crops a subimage.  Given a user-provided set of input constraints,
  the crop window is resampled until it satisfies these constraints.
  If within 100 trials it is unable to find a valid crop, the original
  image is returned. See the Args section for a description of the input
  constraints. Both input boxes and returned Boxes are in normalized
  form (e.g., lie in the unit square [0, 1]).
  This function will return the original image with probability random_coef.

  Note: Keypoint coordinates that are outside the crop will be set to NaN, which
  is consistent with the original keypoint encoding for non-existing keypoints.
  Also, the keypoint visibility will be set to False.

  Args:
    image: rank 3 float32 tensor contains 1 image -> [height, width, channels]
           with pixel values varying between [0, 1].
    boxes: rank 2 float32 tensor containing the bounding boxes with shape
           [num_instances, 4].
           Boxes are in normalized form meaning their coordinates vary
           between [0, 1].
           Each row is in the form of [ymin, xmin, ymax, xmax].
    labels: rank 1 int32 tensor containing the object classes.
    label_weights: float32 tensor of shape [num_instances] representing the
      weight for each box.
    label_confidences: (optional) float32 tensor of shape [num_instances].
      representing the confidence for each box.
    multiclass_scores: (optional) float32 tensor of shape
      [num_instances, num_classes] representing the score for each box for each
      class.
    masks: (optional) rank 3 float32 tensor with shape
           [num_instances, height, width] containing instance masks. The masks
           are of the same height, width as the input `image`.
    mask_weights: (optional) rank 1 float32 tensor with shape [num_instances]
                  containing weights for each instance mask.
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
    random_coef: a random coefficient that defines the chance of getting the
                 original image. If random_coef is 0, we will always get the
                 cropped image, and if it is 1.0, we will always get the
                 original image.
    seed: random seed.
    preprocess_vars_cache: PreprocessorCache object that records previously
                           performed augmentations. Updated in-place. If this
                           function is called multiple times with the same
                           non-null cache, it will perform deterministically.

  Returns:
    image: Image shape will be [new_height, new_width, channels].
    boxes: boxes which is the same rank as input boxes. Boxes are in normalized
           form.
    labels: new labels.

    If label_weights, multiclass_scores, masks, keypoints,
    keypoint_visibilities, densepose_num_points, densepose_part_ids,
    densepose_surface_coords is not None, the function also returns:
    label_weights: rank 1 float32 tensor with shape [num_instances].
    multiclass_scores: rank 2 float32 tensor with shape
                       [num_instances, num_classes]
    masks: rank 3 float32 tensor with shape [num_instances, height, width]
           containing instance masks.
    mask_weights: rank 1 float32 tensor with shape [num_instances].
    keypoints: rank 3 float32 tensor with shape
               [num_instances, num_keypoints, 2]
    keypoint_visibilities: rank 2 bool tensor with shape
                           [num_instances, num_keypoints]
    densepose_num_points: rank 1 int32 tensor with shape [num_instances].
    densepose_part_ids: rank 2 int32 tensor with shape
                        [num_instances, num_points].
    densepose_surface_coords: rank 3 float32 tensor with shape
                              [num_instances, num_points, 4].
  """

  def strict_random_crop_image_fn():
    return _strict_random_crop_image(
        image,
        boxes,
        labels,
        label_weights,
        label_confidences=label_confidences,
        multiclass_scores=multiclass_scores,
        masks=masks,
        mask_weights=mask_weights,
        keypoints=keypoints,
        keypoint_visibilities=keypoint_visibilities,
        densepose_num_points=densepose_num_points,
        densepose_part_ids=densepose_part_ids,
        densepose_surface_coords=densepose_surface_coords,
        min_object_covered=min_object_covered,
        aspect_ratio_range=aspect_ratio_range,
        area_range=area_range,
        overlap_thresh=overlap_thresh,
        clip_boxes=clip_boxes,
        preprocess_vars_cache=preprocess_vars_cache)

  # avoids tf.cond to make faster RCNN training on borg. See b/140057645.
  if random_coef < sys.float_info.min:
    result = strict_random_crop_image_fn()
  else:
    generator_func = functools.partial(tf.random_uniform, [], seed=seed)
    do_a_crop_random = _get_or_create_preprocess_rand_vars(
        generator_func, preprocessor_cache.PreprocessorCache.CROP_IMAGE,
        preprocess_vars_cache)
    do_a_crop_random = tf.greater(do_a_crop_random, random_coef)

    outputs = [image, boxes, labels]

    if label_weights is not None:
      outputs.append(label_weights)
    if label_confidences is not None:
      outputs.append(label_confidences)
    if multiclass_scores is not None:
      outputs.append(multiclass_scores)
    if masks is not None:
      outputs.append(masks)
    if mask_weights is not None:
      outputs.append(mask_weights)
    if keypoints is not None:
      outputs.append(keypoints)
    if keypoint_visibilities is not None:
      outputs.append(keypoint_visibilities)
    if densepose_num_points is not None:
      outputs.extend([densepose_num_points, densepose_part_ids,
                      densepose_surface_coords])

    result = tf.cond(do_a_crop_random, strict_random_crop_image_fn,
                     lambda: tuple(outputs))
  return result