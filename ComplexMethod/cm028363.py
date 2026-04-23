def multi_class_non_max_suppression(box_mask_list, score_thresh, iou_thresh,
                                    max_output_size):
  """Multi-class version of non maximum suppression.

  This op greedily selects a subset of detection bounding boxes, pruning
  away boxes that have high IOU (intersection over union) overlap (> thresh)
  with already selected boxes.  It operates independently for each class for
  which scores are provided (via the scores field of the input box_list),
  pruning boxes with score less than a provided threshold prior to
  applying NMS.

  Args:
    box_mask_list: np_box_mask_list.BoxMaskList holding N boxes.  Must contain a
      'scores' field representing detection scores.  This scores field is a
      tensor that can be 1 dimensional (in the case of a single class) or
      2-dimensional, in which case we assume that it takes the
      shape [num_boxes, num_classes]. We further assume that this rank is known
      statically and that scores.shape[1] is also known (i.e., the number of
      classes is fixed and known at graph construction time).
    score_thresh: scalar threshold for score (low scoring boxes are removed).
    iou_thresh: scalar threshold for IOU (boxes that that high IOU overlap
      with previously selected boxes are removed).
    max_output_size: maximum number of retained boxes per class.

  Returns:
    a box_mask_list holding M boxes with a rank-1 scores field representing
      corresponding scores for each box with scores sorted in decreasing order
      and a rank-1 classes field representing a class label for each box.
  Raises:
    ValueError: if iou_thresh is not in [0, 1] or if input box_mask_list does
      not have a valid scores field.
  """
  if not 0 <= iou_thresh <= 1.0:
    raise ValueError('thresh must be between 0 and 1')
  if not isinstance(box_mask_list, np_box_mask_list.BoxMaskList):
    raise ValueError('box_mask_list must be a box_mask_list')
  if not box_mask_list.has_field('scores'):
    raise ValueError('input box_mask_list must have \'scores\' field')
  scores = box_mask_list.get_field('scores')
  if len(scores.shape) == 1:
    scores = np.reshape(scores, [-1, 1])
  elif len(scores.shape) == 2:
    if scores.shape[1] is None:
      raise ValueError('scores field must have statically defined second '
                       'dimension')
  else:
    raise ValueError('scores field must be of rank 1 or 2')

  num_boxes = box_mask_list.num_boxes()
  num_scores = scores.shape[0]
  num_classes = scores.shape[1]

  if num_boxes != num_scores:
    raise ValueError('Incorrect scores field length: actual vs expected.')

  selected_boxes_list = []
  for class_idx in range(num_classes):
    box_mask_list_and_class_scores = np_box_mask_list.BoxMaskList(
        box_data=box_mask_list.get(),
        mask_data=box_mask_list.get_masks())
    class_scores = np.reshape(scores[0:num_scores, class_idx], [-1])
    box_mask_list_and_class_scores.add_field('scores', class_scores)
    box_mask_list_filt = filter_scores_greater_than(
        box_mask_list_and_class_scores, score_thresh)
    nms_result = non_max_suppression(
        box_mask_list_filt,
        max_output_size=max_output_size,
        iou_threshold=iou_thresh,
        score_threshold=score_thresh)
    nms_result.add_field(
        'classes',
        np.zeros_like(nms_result.get_field('scores')) + class_idx)
    selected_boxes_list.append(nms_result)
  selected_boxes = np_box_list_ops.concatenate(selected_boxes_list)
  sorted_boxes = np_box_list_ops.sort_by_field(selected_boxes, 'scores')
  return box_list_to_box_mask_list(boxlist=sorted_boxes)