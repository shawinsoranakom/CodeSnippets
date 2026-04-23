def multi_class_non_max_suppression(boxlist, score_thresh, iou_thresh,
                                    max_output_size):
  """Multi-class version of non maximum suppression.

  This op greedily selects a subset of detection bounding boxes, pruning
  away boxes that have high IOU (intersection over union) overlap (> thresh)
  with already selected boxes.  It operates independently for each class for
  which scores are provided (via the scores field of the input box_list),
  pruning boxes with score less than a provided threshold prior to
  applying NMS.

  Args:
    boxlist: BoxList holding N boxes.  Must contain a 'scores' field
      representing detection scores.  This scores field is a tensor that can
      be 1 dimensional (in the case of a single class) or 2-dimensional, which
      which case we assume that it takes the shape [num_boxes, num_classes].
      We further assume that this rank is known statically and that
      scores.shape[1] is also known (i.e., the number of classes is fixed
      and known at graph construction time).
    score_thresh: scalar threshold for score (low scoring boxes are removed).
    iou_thresh: scalar threshold for IOU (boxes that that high IOU overlap
      with previously selected boxes are removed).
    max_output_size: maximum number of retained boxes per class.

  Returns:
    a BoxList holding M boxes with a rank-1 scores field representing
      corresponding scores for each box with scores sorted in decreasing order
      and a rank-1 classes field representing a class label for each box.
  Raises:
    ValueError: if iou_thresh is not in [0, 1] or if input boxlist does not have
      a valid scores field.
  """
  if not 0 <= iou_thresh <= 1.0:
    raise ValueError('thresh must be between 0 and 1')
  if not isinstance(boxlist, np_box_list.BoxList):
    raise ValueError('boxlist must be a BoxList')
  if not boxlist.has_field('scores'):
    raise ValueError('input boxlist must have \'scores\' field')
  scores = boxlist.get_field('scores')
  if len(scores.shape) == 1:
    scores = np.reshape(scores, [-1, 1])
  elif len(scores.shape) == 2:
    if scores.shape[1] is None:
      raise ValueError('scores field must have statically defined second '
                       'dimension')
  else:
    raise ValueError('scores field must be of rank 1 or 2')
  num_boxes = boxlist.num_boxes()
  num_scores = scores.shape[0]
  num_classes = scores.shape[1]

  if num_boxes != num_scores:
    raise ValueError('Incorrect scores field length: actual vs expected.')

  selected_boxes_list = []
  for class_idx in range(num_classes):
    boxlist_and_class_scores = np_box_list.BoxList(boxlist.get())
    class_scores = np.reshape(scores[0:num_scores, class_idx], [-1])
    boxlist_and_class_scores.add_field('scores', class_scores)
    boxlist_filt = filter_scores_greater_than(boxlist_and_class_scores,
                                              score_thresh)
    nms_result = non_max_suppression(boxlist_filt,
                                     max_output_size=max_output_size,
                                     iou_threshold=iou_thresh,
                                     score_threshold=score_thresh)
    nms_result.add_field(
        'classes', np.zeros_like(nms_result.get_field('scores')) + class_idx)
    selected_boxes_list.append(nms_result)
  selected_boxes = concatenate(selected_boxes_list)
  sorted_boxes = sort_by_field(selected_boxes, 'scores')
  return sorted_boxes