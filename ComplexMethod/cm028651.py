def transform_and_clip_boxes(boxes,
                             infos,
                             affine=None,
                             shuffle_boxes=False,
                             area_thresh=0.1,
                             seed=None,
                             filter_and_clip_boxes=True):
  """Clips and cleans the boxes.

  Args:
    boxes: A `Tensor` for the boxes.
    infos: A `list` that contains the image infos.
    affine: A `list` that contains parameters for resize and crop.
    shuffle_boxes: A `bool` for shuffling the boxes.
    area_thresh: An `int` for the area threshold.
    seed: seed for random number generation.
    filter_and_clip_boxes: A `bool` for filtering and clipping the boxes to
      [0, 1].

  Returns:
    boxes: A `Tensor` representing the augmented boxes.
    ind: A `Tensor` valid box indices.
  """

  # Clip and clean boxes.
  def get_valid_boxes(boxes):
    """Get indices for non-empty boxes."""
    # Convert the boxes to center width height formatting.
    height = boxes[:, 2] - boxes[:, 0]
    width = boxes[:, 3] - boxes[:, 1]
    base = tf.logical_and(tf.greater(height, 0), tf.greater(width, 0))
    return base

  # Initialize history to track operation applied to boxes
  box_history = boxes

  # Make sure all boxes are valid to start, clip to [0, 1] and get only the
  # valid boxes.
  output_size = None
  if filter_and_clip_boxes:
    boxes = tf.math.maximum(tf.math.minimum(boxes, 1.0), 0.0)
  cond = get_valid_boxes(boxes)

  if infos is None:
    infos = []

  for info in infos:
    # Denormalize the boxes.
    boxes = bbox_ops.denormalize_boxes(boxes, info[0])
    box_history = bbox_ops.denormalize_boxes(box_history, info[0])

    # Shift and scale all boxes, and keep track of box history with no
    # box clipping, history is used for removing boxes that have become
    # too small or exit the image area.
    (boxes, box_history) = resize_and_crop_boxes(
        boxes, info[2, :], info[1, :], info[3, :], box_history=box_history)

    # Get all the boxes that still remain in the image and store
    # in a bit vector for later use.
    cond = tf.logical_and(get_valid_boxes(boxes), cond)

    # Normalize the boxes to [0, 1].
    output_size = info[1]
    boxes = bbox_ops.normalize_boxes(boxes, output_size)
    box_history = bbox_ops.normalize_boxes(box_history, output_size)

  if affine is not None:
    # Denormalize the boxes.
    boxes = bbox_ops.denormalize_boxes(boxes, affine[0])
    box_history = bbox_ops.denormalize_boxes(box_history, affine[0])

    # Clipped final boxes.
    (boxes, box_history) = affine_warp_boxes(
        affine[2], boxes, affine[1], box_history=box_history)

    # Get all the boxes that still remain in the image and store
    # in a bit vector for later use.
    cond = tf.logical_and(get_valid_boxes(boxes), cond)

    # Normalize the boxes to [0, 1].
    output_size = affine[1]
    boxes = bbox_ops.normalize_boxes(boxes, output_size)
    box_history = bbox_ops.normalize_boxes(box_history, output_size)

  # Remove the bad boxes.
  boxes *= tf.cast(tf.expand_dims(cond, axis=-1), boxes.dtype)

  # Threshold the existing boxes.
  if filter_and_clip_boxes:
    if output_size is not None:
      boxes_ = bbox_ops.denormalize_boxes(boxes, output_size)
      box_history_ = bbox_ops.denormalize_boxes(box_history, output_size)
      inds = boxes_candidates(boxes_, box_history_, area_thr=area_thresh)
    else:
      inds = boxes_candidates(
          boxes, box_history, wh_thr=0.0, area_thr=area_thresh)
    # Select and gather the good boxes.
    if shuffle_boxes:
      inds = tf.random.shuffle(inds, seed=seed)
  else:
    inds = bbox_ops.get_non_empty_box_indices(boxes)
  boxes = tf.gather(boxes, inds)
  return boxes, inds