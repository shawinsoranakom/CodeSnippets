def non_max_suppression(boxlist,
                        max_output_size=10000,
                        iou_threshold=1.0,
                        score_threshold=-10.0):
  """Non maximum suppression.

  This op greedily selects a subset of detection bounding boxes, pruning
  away boxes that have high IOU (intersection over union) overlap (> thresh)
  with already selected boxes. In each iteration, the detected bounding box with
  highest score in the available pool is selected.

  Args:
    boxlist: BoxList holding N boxes.  Must contain a 'scores' field
      representing detection scores. All scores belong to the same class.
    max_output_size: maximum number of retained boxes
    iou_threshold: intersection over union threshold.
    score_threshold: minimum score threshold. Remove the boxes with scores
                     less than this value. Default value is set to -10. A very
                     low threshold to pass pretty much all the boxes, unless
                     the user sets a different score threshold.

  Returns:
    a BoxList holding M boxes where M <= max_output_size
  Raises:
    ValueError: if 'scores' field does not exist
    ValueError: if threshold is not in [0, 1]
    ValueError: if max_output_size < 0
  """
  if not boxlist.has_field('scores'):
    raise ValueError('Field scores does not exist')
  if iou_threshold < 0. or iou_threshold > 1.0:
    raise ValueError('IOU threshold must be in [0, 1]')
  if max_output_size < 0:
    raise ValueError('max_output_size must be bigger than 0.')

  boxlist = filter_scores_greater_than(boxlist, score_threshold)
  if boxlist.num_boxes() == 0:
    return boxlist

  boxlist = sort_by_field(boxlist, 'scores')

  # Prevent further computation if NMS is disabled.
  if iou_threshold == 1.0:
    if boxlist.num_boxes() > max_output_size:
      selected_indices = np.arange(max_output_size)
      return gather(boxlist, selected_indices)
    else:
      return boxlist

  boxes = boxlist.get()
  num_boxes = boxlist.num_boxes()
  # is_index_valid is True only for all remaining valid boxes,
  is_index_valid = np.full(num_boxes, 1, dtype=bool)
  selected_indices = []
  num_output = 0
  for i in range(num_boxes):
    if num_output < max_output_size:
      if is_index_valid[i]:
        num_output += 1
        selected_indices.append(i)
        is_index_valid[i] = False
        valid_indices = np.where(is_index_valid)[0]
        if valid_indices.size == 0:
          break

        intersect_over_union = np_box_ops.iou(
            np.expand_dims(boxes[i, :], axis=0), boxes[valid_indices, :])
        intersect_over_union = np.squeeze(intersect_over_union, axis=0)
        is_index_valid[valid_indices] = np.logical_and(
            is_index_valid[valid_indices],
            intersect_over_union <= iou_threshold)
  return gather(boxlist, np.array(selected_indices))