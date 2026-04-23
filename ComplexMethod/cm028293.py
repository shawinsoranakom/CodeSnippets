def random_jitter_boxes(boxes, ratio=0.05, jitter_mode='default', seed=None):
  """Randomly jitters boxes in image.

  Args:
    boxes: rank 2 float32 tensor containing the bounding boxes -> [N, 4].
           Boxes are in normalized form meaning their coordinates vary
           between [0, 1].
           Each row is in the form of [ymin, xmin, ymax, xmax].
    ratio: The ratio of the box width and height that the corners can jitter.
           For example if the width is 100 pixels and ratio is 0.05,
           the corners can jitter up to 5 pixels in the x direction.
    jitter_mode: One of
      shrink - Only shrinks boxes.
      expand - Only expands boxes.
      expand_symmetric - Expands the boxes symmetrically along height and width
        dimensions without changing the box center. The ratios of expansion
        along X, Y dimensions are independent
      shrink_symmetric - Shrinks the boxes symmetrically along height and width
        dimensions without changing the box center. The ratios of shrinking
        along X, Y dimensions are independent
      expand_symmetric_xy - Expands the boxes symetrically along height and
        width dimensions and the ratio of expansion is same for both.
      shrink_symmetric_xy - Shrinks the boxes symetrically along height and
        width dimensions and the ratio of shrinking is same for both.
      default - Randomly and independently perturbs each box boundary.
    seed: random seed.

  Returns:
    boxes: boxes which is the same shape as input boxes.
  """
  with tf.name_scope('RandomJitterBoxes'):
    ymin, xmin, ymax, xmax = (boxes[:, i] for i in range(4))

    blist = box_list.BoxList(boxes)
    ycenter, xcenter, height, width = blist.get_center_coordinates_and_sizes()

    height = tf.maximum(tf.abs(height), 1e-6)
    width = tf.maximum(tf.abs(width), 1e-6)

    if jitter_mode in ['shrink', 'shrink_symmetric', 'shrink_symmetric_xy']:
      min_ratio, max_ratio = -ratio, 0
    elif jitter_mode in ['expand', 'expand_symmetric', 'expand_symmetric_xy']:
      min_ratio, max_ratio = 0, ratio
    elif jitter_mode == 'default':
      min_ratio, max_ratio = -ratio, ratio
    else:
      raise ValueError('Unknown jitter mode - %s' % jitter_mode)

    num_boxes = tf.shape(boxes)[0]

    if jitter_mode in ['expand_symmetric', 'shrink_symmetric',
                       'expand_symmetric_xy', 'shrink_symmetric_xy']:
      distortion = 1.0 + tf.random.uniform(
          [num_boxes, 2], minval=min_ratio, maxval=max_ratio, dtype=tf.float32,
          seed=seed)
      height_distortion = distortion[:, 0]
      width_distortion = distortion[:, 1]

      # This is to ensure that all boxes are augmented symmetrically. We clip
      # each boundary to lie within the image, and when doing so, we also
      # adjust its symmetric counterpart.
      max_height_distortion = tf.abs(tf.minimum(
          (2.0 * ycenter) / height, 2.0 * (1 - ycenter) / height))
      max_width_distortion = tf.abs(tf.minimum(
          (2.0 * xcenter) / width, 2.0 * (1 - xcenter) / width))

      if jitter_mode in ['expand_symmetric_xy', 'shrink_symmetric_xy']:
        height_distortion = width_distortion = distortion[:, 0]
        max_height_distortion = max_width_distortion = (
            tf.minimum(max_width_distortion, max_height_distortion))

      height_distortion = tf.clip_by_value(
          height_distortion, -max_height_distortion, max_height_distortion)
      width_distortion = tf.clip_by_value(
          width_distortion, -max_width_distortion, max_width_distortion)

      ymin = ycenter - (height * height_distortion / 2.0)
      ymax = ycenter + (height * height_distortion / 2.0)
      xmin = xcenter - (width * width_distortion / 2.0)
      xmax = xcenter + (width * width_distortion / 2.0)

    elif jitter_mode in ['expand', 'shrink', 'default']:
      distortion = 1.0 + tf.random.uniform(
          [num_boxes, 4], minval=min_ratio, maxval=max_ratio, dtype=tf.float32,
          seed=seed)
      ymin_jitter = height * distortion[:, 0]
      xmin_jitter = width * distortion[:, 1]
      ymax_jitter = height * distortion[:, 2]
      xmax_jitter = width * distortion[:, 3]

      ymin, ymax = ycenter - (ymin_jitter / 2.0), ycenter + (ymax_jitter / 2.0)
      xmin, xmax = xcenter - (xmin_jitter / 2.0), xcenter + (xmax_jitter / 2.0)

    else:
      raise ValueError('Unknown jitter mode - %s' % jitter_mode)

    boxes = tf.stack([ymin, xmin, ymax, xmax], axis=1)
    return tf.clip_by_value(boxes, 0.0, 1.0)