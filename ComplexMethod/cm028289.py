def class_agnostic_non_max_suppression(boxes,
                                       scores,
                                       score_thresh,
                                       iou_thresh,
                                       max_classes_per_detection=1,
                                       max_total_size=0,
                                       clip_window=None,
                                       change_coordinate_frame=False,
                                       masks=None,
                                       boundaries=None,
                                       pad_to_max_output_size=False,
                                       use_partitioned_nms=False,
                                       additional_fields=None,
                                       soft_nms_sigma=0.0,
                                       scope=None):
  """Class-agnostic version of non maximum suppression.

  This op greedily selects a subset of detection bounding boxes, pruning
  away boxes that have high IOU (intersection over union) overlap (> thresh)
  with already selected boxes.  It operates on all the boxes using
  max scores across all classes for which scores are provided (via the scores
  field of the input box_list), pruning boxes with score less than a provided
  threshold prior to applying NMS.

  Please note that this operation is performed in a class-agnostic way,
  therefore any background classes should be removed prior to calling this
  function.

  Selected boxes are guaranteed to be sorted in decreasing order by score (but
  the sort is not guaranteed to be stable).

  Args:
    boxes: A [k, q, 4] float32 tensor containing k detections. `q` can be either
      number of classes or 1 depending on whether a separate box is predicted
      per class.
    scores: A [k, num_classes] float32 tensor containing the scores for each of
      the k detections. The scores have to be non-negative when
      pad_to_max_output_size is True.
    score_thresh: scalar threshold for score (low scoring boxes are removed).
    iou_thresh: scalar threshold for IOU (new boxes that have high IOU overlap
      with previously selected boxes are removed).
    max_classes_per_detection: maximum number of retained classes per detection
      box in class-agnostic NMS.
    max_total_size: maximum number of boxes retained over all classes. By
      default returns all boxes retained after capping boxes per class.
    clip_window: A float32 tensor of the form [y_min, x_min, y_max, x_max]
      representing the window to clip and normalize boxes to before performing
      non-max suppression.
    change_coordinate_frame: Whether to normalize coordinates after clipping
      relative to clip_window (this can only be set to True if a clip_window is
      provided)
    masks: (optional) a [k, q, mask_height, mask_width] float32 tensor
      containing box masks. `q` can be either number of classes or 1 depending
      on whether a separate mask is predicted per class.
    boundaries: (optional) a [k, q, boundary_height, boundary_width] float32
      tensor containing box boundaries. `q` can be either number of classes or 1
      depending on whether a separate boundary is predicted per class.
    pad_to_max_output_size: If true, the output nmsed boxes are padded to be of
      length `max_size_per_class`. Defaults to false.
    use_partitioned_nms: If true, use partitioned version of
      non_max_suppression.
    additional_fields: (optional) If not None, a dictionary that maps keys to
      tensors whose first dimensions are all of size `k`. After non-maximum
      suppression, all tensors corresponding to the selected boxes will be added
      to resulting BoxList.
    soft_nms_sigma: A scalar float representing the Soft NMS sigma parameter;
      See Bodla et al, https://arxiv.org/abs/1704.04503).  When
      `soft_nms_sigma=0.0` (which is default), we fall back to standard (hard)
      NMS.  Soft NMS is currently only supported when pad_to_max_output_size is
      False.
    scope: name scope.

  Returns:
    A tuple of sorted_boxes and num_valid_nms_boxes. The sorted_boxes is a
      BoxList holds M boxes with a rank-1 scores field representing
      corresponding scores for each box with scores sorted in decreasing order
      and a rank-1 classes field representing a class label for each box. The
      num_valid_nms_boxes is a 0-D integer tensor representing the number of
      valid elements in `BoxList`, with the valid elements appearing first.

  Raises:
    ValueError: if iou_thresh is not in [0, 1] or if input boxlist does not have
      a valid scores field or if non-zero soft_nms_sigma is provided when
      pad_to_max_output_size is True.
  """
  _validate_boxes_scores_iou_thresh(boxes, scores, iou_thresh,
                                    change_coordinate_frame, clip_window)
  if pad_to_max_output_size and soft_nms_sigma != 0.0:
    raise ValueError('Soft NMS (soft_nms_sigma != 0.0) is currently not '
                     'supported when pad_to_max_output_size is True.')

  if max_classes_per_detection > 1:
    raise ValueError('Max classes per detection box >1 not supported.')
  q = shape_utils.get_dim_as_int(boxes.shape[1])
  if q > 1:
    class_ids = tf.expand_dims(
        tf.argmax(scores, axis=1, output_type=tf.int32), axis=1)
    boxes = tf.batch_gather(boxes, class_ids)
    if masks is not None:
      masks = tf.batch_gather(masks, class_ids)
    if boundaries is not None:
      boundaries = tf.batch_gather(boundaries, class_ids)
  boxes = tf.squeeze(boxes, axis=[1])
  if masks is not None:
    masks = tf.squeeze(masks, axis=[1])
  if boundaries is not None:
    boundaries = tf.squeeze(boundaries, axis=[1])

  with tf.name_scope(scope, 'ClassAgnosticNonMaxSuppression'):
    boxlist_and_class_scores = box_list.BoxList(boxes)
    max_scores = tf.reduce_max(scores, axis=-1)
    classes_with_max_scores = tf.argmax(scores, axis=-1)
    boxlist_and_class_scores.add_field(fields.BoxListFields.scores, max_scores)
    if masks is not None:
      boxlist_and_class_scores.add_field(fields.BoxListFields.masks, masks)
    if boundaries is not None:
      boxlist_and_class_scores.add_field(fields.BoxListFields.boundaries,
                                         boundaries)

    if additional_fields is not None:
      for key, tensor in additional_fields.items():
        boxlist_and_class_scores.add_field(key, tensor)

    nms_result = None
    selected_scores = None
    if pad_to_max_output_size:
      max_selection_size = max_total_size
      if use_partitioned_nms:
        (selected_indices, num_valid_nms_boxes,
         boxlist_and_class_scores.data['boxes'],
         boxlist_and_class_scores.data['scores'],
         argsort_ids) = partitioned_non_max_suppression_padded(
             boxlist_and_class_scores.get(),
             boxlist_and_class_scores.get_field(fields.BoxListFields.scores),
             max_selection_size,
             iou_threshold=iou_thresh,
             score_threshold=score_thresh)
        classes_with_max_scores = tf.gather(classes_with_max_scores,
                                            argsort_ids)
      else:
        selected_indices, num_valid_nms_boxes = (
            tf.image.non_max_suppression_padded(
                boxlist_and_class_scores.get(),
                boxlist_and_class_scores.get_field(fields.BoxListFields.scores),
                max_selection_size,
                iou_threshold=iou_thresh,
                score_threshold=score_thresh,
                pad_to_max_output_size=True))
      nms_result = box_list_ops.gather(boxlist_and_class_scores,
                                       selected_indices)
      selected_scores = nms_result.get_field(fields.BoxListFields.scores)
    else:
      max_selection_size = tf.minimum(max_total_size,
                                      boxlist_and_class_scores.num_boxes())
      if (hasattr(tf.image, 'non_max_suppression_with_scores') and
          tf.compat.forward_compatible(2019, 6, 6)):
        (selected_indices, selected_scores
        ) = tf.image.non_max_suppression_with_scores(
            boxlist_and_class_scores.get(),
            boxlist_and_class_scores.get_field(fields.BoxListFields.scores),
            max_selection_size,
            iou_threshold=iou_thresh,
            score_threshold=score_thresh,
            soft_nms_sigma=soft_nms_sigma)
        num_valid_nms_boxes = tf.shape(selected_indices)[0]
        selected_indices = tf.concat([
            selected_indices,
            tf.zeros(max_selection_size - num_valid_nms_boxes, tf.int32)
        ], 0)
        selected_scores = tf.concat(
            [selected_scores,
             tf.zeros(max_selection_size-num_valid_nms_boxes, tf.float32)], -1)
        nms_result = box_list_ops.gather(boxlist_and_class_scores,
                                         selected_indices)
      else:
        if soft_nms_sigma != 0:
          raise ValueError('Soft NMS not supported in current TF version!')
        selected_indices = tf.image.non_max_suppression(
            boxlist_and_class_scores.get(),
            boxlist_and_class_scores.get_field(fields.BoxListFields.scores),
            max_selection_size,
            iou_threshold=iou_thresh,
            score_threshold=score_thresh)
        num_valid_nms_boxes = tf.shape(selected_indices)[0]
        selected_indices = tf.concat(
            [selected_indices,
             tf.zeros(max_selection_size-num_valid_nms_boxes, tf.int32)], 0)
        nms_result = box_list_ops.gather(boxlist_and_class_scores,
                                         selected_indices)
        selected_scores = nms_result.get_field(fields.BoxListFields.scores)
    valid_nms_boxes_indices = tf.less(
        tf.range(max_selection_size), num_valid_nms_boxes)
    nms_result.add_field(
        fields.BoxListFields.scores,
        tf.where(valid_nms_boxes_indices,
                 selected_scores, -1*tf.ones(max_selection_size)))

    selected_classes = tf.gather(classes_with_max_scores, selected_indices)
    selected_classes = tf.cast(selected_classes, tf.float32)
    nms_result.add_field(fields.BoxListFields.classes, selected_classes)
    selected_boxes = nms_result
    sorted_boxes = box_list_ops.sort_by_field(selected_boxes,
                                              fields.BoxListFields.scores)

    if clip_window is not None:
      # When pad_to_max_output_size is False, it prunes the boxes with zero
      # area.
      sorted_boxes, num_valid_nms_boxes = _clip_window_prune_boxes(
          sorted_boxes, clip_window, pad_to_max_output_size,
          change_coordinate_frame)

    if max_total_size:
      max_total_size = tf.minimum(max_total_size, sorted_boxes.num_boxes())
      sorted_boxes = box_list_ops.gather(sorted_boxes, tf.range(max_total_size))
      num_valid_nms_boxes = tf.where(max_total_size > num_valid_nms_boxes,
                                     num_valid_nms_boxes, max_total_size)
    # Select only the valid boxes if pad_to_max_output_size is False.
    if not pad_to_max_output_size:
      sorted_boxes = box_list_ops.gather(sorted_boxes,
                                         tf.range(num_valid_nms_boxes))

    return sorted_boxes, num_valid_nms_boxes