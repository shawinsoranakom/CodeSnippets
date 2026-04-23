def random_horizontal_flip(image,
                           boxes=None,
                           masks=None,
                           keypoints=None,
                           keypoint_visibilities=None,
                           densepose_part_ids=None,
                           densepose_surface_coords=None,
                           keypoint_depths=None,
                           keypoint_depth_weights=None,
                           keypoint_flip_permutation=None,
                           probability=0.5,
                           seed=None,
                           preprocess_vars_cache=None):
  """Randomly flips the image and detections horizontally.

  Args:
    image: rank 3 float32 tensor with shape [height, width, channels].
    boxes: (optional) rank 2 float32 tensor with shape [N, 4]
           containing the bounding boxes.
           Boxes are in normalized form meaning their coordinates vary
           between [0, 1].
           Each row is in the form of [ymin, xmin, ymax, xmax].
    masks: (optional) rank 3 float32 tensor with shape
           [num_instances, height, width] containing instance masks. The masks
           are of the same height, width as the input `image`.
    keypoints: (optional) rank 3 float32 tensor with shape
               [num_instances, num_keypoints, 2]. The keypoints are in y-x
               normalized coordinates.
    keypoint_visibilities: (optional) rank 2 bool tensor with shape
                           [num_instances, num_keypoints].
    densepose_part_ids: (optional) rank 2 int32 tensor with shape
                        [num_instances, num_points] holding the part id for each
                        sampled point. These part_ids are 0-indexed, where the
                        first non-background part has index 0.
    densepose_surface_coords: (optional) rank 3 float32 tensor with shape
                              [num_instances, num_points, 4]. The DensePose
                              coordinates are of the form (y, x, v, u)  where
                              (y, x) are the normalized image coordinates for a
                              sampled point, and (v, u) is the surface
                              coordinate for the part.
    keypoint_depths: (optional) rank 2 float32 tensor with shape [num_instances,
                     num_keypoints] representing the relative depth of the
                     keypoints.
    keypoint_depth_weights: (optional) rank 2 float32 tensor with shape
                            [num_instances, num_keypoints] representing the
                            weights of the relative depth of the keypoints.
    keypoint_flip_permutation: rank 1 int32 tensor containing the keypoint flip
                               permutation.
    probability: the probability of performing this augmentation.
    seed: random seed
    preprocess_vars_cache: PreprocessorCache object that records previously
                           performed augmentations. Updated in-place. If this
                           function is called multiple times with the same
                           non-null cache, it will perform deterministically.

  Returns:
    image: image which is the same shape as input image.

    If boxes, masks, keypoints, keypoint_visibilities,
    keypoint_flip_permutation, densepose_part_ids, or densepose_surface_coords
    are not None,the function also returns the following tensors.

    boxes: rank 2 float32 tensor containing the bounding boxes -> [N, 4].
           Boxes are in normalized form meaning their coordinates vary
           between [0, 1].
    masks: rank 3 float32 tensor with shape [num_instances, height, width]
           containing instance masks.
    keypoints: rank 3 float32 tensor with shape
               [num_instances, num_keypoints, 2]
    keypoint_visibilities: rank 2 bool tensor with shape
                           [num_instances, num_keypoints].
    densepose_part_ids: rank 2 int32 tensor with shape
                        [num_instances, num_points].
    densepose_surface_coords: rank 3 float32 tensor with shape
                              [num_instances, num_points, 4].
    keypoint_depths: rank 2 float32 tensor with shape [num_instances,
                     num_keypoints]
    keypoint_depth_weights: rank 2 float32 tensor with shape [num_instances,
                            num_keypoints].

  Raises:
    ValueError: if keypoints are provided but keypoint_flip_permutation is not.
    ValueError: if either densepose_part_ids or densepose_surface_coords is
                not None, but both are not None.
  """

  def _flip_image(image):
    # flip image
    image_flipped = tf.image.flip_left_right(image)
    return image_flipped

  if keypoints is not None and keypoint_flip_permutation is None:
    raise ValueError(
        'keypoints are provided but keypoints_flip_permutation is not provided')

  if ((densepose_part_ids is not None and densepose_surface_coords is None) or
      (densepose_part_ids is None and densepose_surface_coords is not None)):
    raise ValueError(
        'Must provide both `densepose_part_ids` and `densepose_surface_coords`')

  with tf.name_scope('RandomHorizontalFlip', values=[image, boxes]):
    result = []
    # random variable defining whether to do flip or not
    generator_func = functools.partial(tf.random_uniform, [], seed=seed)
    do_a_flip_random = _get_or_create_preprocess_rand_vars(
        generator_func,
        preprocessor_cache.PreprocessorCache.HORIZONTAL_FLIP,
        preprocess_vars_cache)
    do_a_flip_random = tf.less(do_a_flip_random, probability)

    # flip image
    image = tf.cond(do_a_flip_random, lambda: _flip_image(image), lambda: image)
    result.append(image)

    # flip boxes
    if boxes is not None:
      boxes = tf.cond(do_a_flip_random, lambda: _flip_boxes_left_right(boxes),
                      lambda: boxes)
      result.append(boxes)

    # flip masks
    if masks is not None:
      masks = tf.cond(do_a_flip_random, lambda: _flip_masks_left_right(masks),
                      lambda: masks)
      result.append(masks)

    # flip keypoints
    if keypoints is not None and keypoint_flip_permutation is not None:
      permutation = keypoint_flip_permutation
      keypoints = tf.cond(
          do_a_flip_random,
          lambda: keypoint_ops.flip_horizontal(keypoints, 0.5, permutation),
          lambda: keypoints)
      result.append(keypoints)

    # flip keypoint visibilities
    if (keypoint_visibilities is not None and
        keypoint_flip_permutation is not None):
      kpt_flip_perm = keypoint_flip_permutation
      keypoint_visibilities = tf.cond(
          do_a_flip_random,
          lambda: tf.gather(keypoint_visibilities, kpt_flip_perm, axis=1),
          lambda: keypoint_visibilities)
      result.append(keypoint_visibilities)

    # flip DensePose parts and coordinates
    if densepose_part_ids is not None:
      flip_densepose_fn = functools.partial(
          densepose_ops.flip_horizontal, densepose_part_ids,
          densepose_surface_coords)
      densepose_tensors = tf.cond(
          do_a_flip_random,
          flip_densepose_fn,
          lambda: (densepose_part_ids, densepose_surface_coords))
      result.extend(densepose_tensors)

    # flip keypoint depths and weights.
    if (keypoint_depths is not None and
        keypoint_flip_permutation is not None):
      kpt_flip_perm = keypoint_flip_permutation
      keypoint_depths = tf.cond(
          do_a_flip_random,
          lambda: tf.gather(keypoint_depths, kpt_flip_perm, axis=1),
          lambda: keypoint_depths)
      keypoint_depth_weights = tf.cond(
          do_a_flip_random,
          lambda: tf.gather(keypoint_depth_weights, kpt_flip_perm, axis=1),
          lambda: keypoint_depth_weights)
      result.append(keypoint_depths)
      result.append(keypoint_depth_weights)

    return tuple(result)