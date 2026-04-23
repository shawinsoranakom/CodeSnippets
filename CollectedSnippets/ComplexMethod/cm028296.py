def random_pad_image(image,
                     boxes,
                     masks=None,
                     keypoints=None,
                     densepose_surface_coords=None,
                     min_image_size=None,
                     max_image_size=None,
                     pad_color=None,
                     center_pad=False,
                     seed=None,
                     preprocess_vars_cache=None):
  """Randomly pads the image.

  This function randomly pads the image with zeros. The final size of the
  padded image will be between min_image_size and max_image_size.
  if min_image_size is smaller than the input image size, min_image_size will
  be set to the input image size. The same for max_image_size. The input image
  will be located at a uniformly random location inside the padded image.
  The relative location of the boxes to the original image will remain the same.

  Args:
    image: rank 3 float32 tensor containing 1 image -> [height, width, channels]
           with pixel values varying between [0, 1].
    boxes: rank 2 float32 tensor containing the bounding boxes -> [N, 4].
           Boxes are in normalized form meaning their coordinates vary
           between [0, 1].
           Each row is in the form of [ymin, xmin, ymax, xmax].
    masks: (optional) rank 3 float32 tensor with shape
           [N, height, width] containing instance masks. The masks
           are of the same height, width as the input `image`.
    keypoints: (optional) rank 3 float32 tensor with shape
               [N, num_keypoints, 2]. The keypoints are in y-x normalized
               coordinates.
    densepose_surface_coords: (optional) rank 3 float32 tensor with shape
                              [N, num_points, 4]. The DensePose coordinates are
                              of the form (y, x, v, u) where (y, x) are the
                              normalized image coordinates for a sampled point,
                              and (v, u) is the surface coordinate for the part.
    min_image_size: a tensor of size [min_height, min_width], type tf.int32.
                    If passed as None, will be set to image size
                    [height, width].
    max_image_size: a tensor of size [max_height, max_width], type tf.int32.
                    If passed as None, will be set to twice the
                    image [height * 2, width * 2].
    pad_color: padding color. A rank 1 tensor of [channels] with dtype=
               tf.float32. if set as None, it will be set to average color of
               the input image.
    center_pad: whether the original image will be padded to the center, or
                randomly padded (which is default).
    seed: random seed.
    preprocess_vars_cache: PreprocessorCache object that records previously
                           performed augmentations. Updated in-place. If this
                           function is called multiple times with the same
                           non-null cache, it will perform deterministically.

  Returns:
    image: Image shape will be [new_height, new_width, channels].
    boxes: boxes which is the same rank as input boxes. Boxes are in normalized
           form.

    if masks is not None, the function also returns:
    masks: rank 3 float32 tensor with shape [N, new_height, new_width]
    if keypoints is not None, the function also returns:
    keypoints: rank 3 float32 tensor with shape [N, num_keypoints, 2]
    if densepose_surface_coords is not None, the function also returns:
    densepose_surface_coords: rank 3 float32 tensor with shape
      [num_instances, num_points, 4]
  """
  if pad_color is None:
    pad_color = tf.reduce_mean(image, axis=[0, 1])

  image_shape = tf.shape(image)
  image_height = image_shape[0]
  image_width = image_shape[1]

  if max_image_size is None:
    max_image_size = tf.stack([image_height * 2, image_width * 2])
  max_image_size = tf.maximum(max_image_size,
                              tf.stack([image_height, image_width]))

  if min_image_size is None:
    min_image_size = tf.stack([image_height, image_width])
  min_image_size = tf.maximum(min_image_size,
                              tf.stack([image_height, image_width]))

  target_height = tf.cond(
      max_image_size[0] > min_image_size[0],
      lambda: _random_integer(min_image_size[0], max_image_size[0], seed),
      lambda: max_image_size[0])

  target_width = tf.cond(
      max_image_size[1] > min_image_size[1],
      lambda: _random_integer(min_image_size[1], max_image_size[1], seed),
      lambda: max_image_size[1])

  offset_height = tf.cond(
      target_height > image_height,
      lambda: _random_integer(0, target_height - image_height, seed),
      lambda: tf.constant(0, dtype=tf.int32))

  offset_width = tf.cond(
      target_width > image_width,
      lambda: _random_integer(0, target_width - image_width, seed),
      lambda: tf.constant(0, dtype=tf.int32))

  if center_pad:
    offset_height = tf.cast(tf.floor((target_height - image_height) / 2),
                            tf.int32)
    offset_width = tf.cast(tf.floor((target_width - image_width) / 2),
                           tf.int32)

  gen_func = lambda: (target_height, target_width, offset_height, offset_width)
  params = _get_or_create_preprocess_rand_vars(
      gen_func, preprocessor_cache.PreprocessorCache.PAD_IMAGE,
      preprocess_vars_cache)
  target_height, target_width, offset_height, offset_width = params

  new_image = tf.image.pad_to_bounding_box(
      image,
      offset_height=offset_height,
      offset_width=offset_width,
      target_height=target_height,
      target_width=target_width)

  # Setting color of the padded pixels
  image_ones = tf.ones_like(image)
  image_ones_padded = tf.image.pad_to_bounding_box(
      image_ones,
      offset_height=offset_height,
      offset_width=offset_width,
      target_height=target_height,
      target_width=target_width)
  image_color_padded = (1.0 - image_ones_padded) * pad_color
  new_image += image_color_padded

  # setting boxes
  new_window = tf.cast(
      tf.stack([
          -offset_height, -offset_width, target_height - offset_height,
          target_width - offset_width
      ]),
      dtype=tf.float32)
  new_window /= tf.cast(
      tf.stack([image_height, image_width, image_height, image_width]),
      dtype=tf.float32)
  boxlist = box_list.BoxList(boxes)
  new_boxlist = box_list_ops.change_coordinate_frame(boxlist, new_window)
  new_boxes = new_boxlist.get()

  result = [new_image, new_boxes]

  if masks is not None:
    new_masks = tf.image.pad_to_bounding_box(
        masks[:, :, :, tf.newaxis],
        offset_height=offset_height,
        offset_width=offset_width,
        target_height=target_height,
        target_width=target_width)[:, :, :, 0]
    result.append(new_masks)

  if keypoints is not None:
    new_keypoints = keypoint_ops.change_coordinate_frame(keypoints, new_window)
    result.append(new_keypoints)

  if densepose_surface_coords is not None:
    new_densepose_surface_coords = densepose_ops.change_coordinate_frame(
        densepose_surface_coords, new_window)
    result.append(new_densepose_surface_coords)

  return tuple(result)