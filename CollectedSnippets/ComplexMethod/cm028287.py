def _validate_boxes_scores_iou_thresh(boxes, scores, iou_thresh,
                                      change_coordinate_frame, clip_window):
  """Validates boxes, scores and iou_thresh.

  This function validates the boxes, scores, iou_thresh
     and if change_coordinate_frame is True, clip_window must be specified.

  Args:
    boxes: A [k, q, 4] float32 tensor containing k detections. `q` can be either
      number of classes or 1 depending on whether a separate box is predicted
      per class.
    scores: A [k, num_classes] float32 tensor containing the scores for each of
      the k detections. The scores have to be non-negative when
      pad_to_max_output_size is True.
    iou_thresh: scalar threshold for IOU (new boxes that have high IOU overlap
      with previously selected boxes are removed).
    change_coordinate_frame: Whether to normalize coordinates after clipping
      relative to clip_window (this can only be set to True if a clip_window is
      provided)
    clip_window: A float32 tensor of the form [y_min, x_min, y_max, x_max]
      representing the window to clip and normalize boxes to before performing
      non-max suppression.

  Raises:
    ValueError: if iou_thresh is not in [0, 1] or if input boxlist does not
    have a valid scores field.
  """
  if not 0 <= iou_thresh <= 1.0:
    raise ValueError('iou_thresh must be between 0 and 1')
  if scores.shape.ndims != 2:
    raise ValueError('scores field must be of rank 2')
  if shape_utils.get_dim_as_int(scores.shape[1]) is None:
    raise ValueError('scores must have statically defined second ' 'dimension')
  if boxes.shape.ndims != 3:
    raise ValueError('boxes must be of rank 3.')
  if not (shape_utils.get_dim_as_int(
      boxes.shape[1]) == shape_utils.get_dim_as_int(scores.shape[1]) or
          shape_utils.get_dim_as_int(boxes.shape[1]) == 1):
    raise ValueError('second dimension of boxes must be either 1 or equal '
                     'to the second dimension of scores')
  if shape_utils.get_dim_as_int(boxes.shape[2]) != 4:
    raise ValueError('last dimension of boxes must be of size 4.')
  if change_coordinate_frame and clip_window is None:
    raise ValueError('if change_coordinate_frame is True, then a clip_window'
                     'must be specified.')