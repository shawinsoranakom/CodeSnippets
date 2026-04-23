def batch_multiclass_non_max_suppression(boxes,
                                         scores,
                                         score_thresh,
                                         iou_thresh,
                                         max_size_per_class,
                                         max_total_size=0,
                                         clip_window=None,
                                         change_coordinate_frame=False,
                                         num_valid_boxes=None,
                                         masks=None,
                                         additional_fields=None,
                                         soft_nms_sigma=0.0,
                                         scope=None,
                                         use_static_shapes=False,
                                         use_partitioned_nms=False,
                                         parallel_iterations=32,
                                         use_class_agnostic_nms=False,
                                         max_classes_per_detection=1,
                                         use_dynamic_map_fn=False,
                                         use_combined_nms=False,
                                         use_hard_nms=False,
                                         use_cpu_nms=False):
  """Multi-class version of non maximum suppression that operates on a batch.

  This op is similar to `multiclass_non_max_suppression` but operates on a batch
  of boxes and scores. See documentation for `multiclass_non_max_suppression`
  for details.

  Args:
    boxes: A [batch_size, num_anchors, q, 4] float32 tensor containing
      detections. If `q` is 1 then same boxes are used for all classes
      otherwise, if `q` is equal to number of classes, class-specific boxes are
      used.
    scores: A [batch_size, num_anchors, num_classes] float32 tensor containing
      the scores for each of the `num_anchors` detections. The scores have to be
      non-negative when use_static_shapes is set True.
    score_thresh: scalar threshold for score (low scoring boxes are removed).
    iou_thresh: scalar threshold for IOU (new boxes that have high IOU overlap
      with previously selected boxes are removed).
    max_size_per_class: maximum number of retained boxes per class.
    max_total_size: maximum number of boxes retained over all classes. By
      default returns all boxes retained after capping boxes per class.
    clip_window: A float32 tensor of shape [batch_size, 4]  where each entry is
      of the form [y_min, x_min, y_max, x_max] representing the window to clip
      boxes to before performing non-max suppression. This argument can also be
      a tensor of shape [4] in which case, the same clip window is applied to
      all images in the batch. If clip_widow is None, all boxes are used to
      perform non-max suppression.
    change_coordinate_frame: Whether to normalize coordinates after clipping
      relative to clip_window (this can only be set to True if a clip_window is
      provided)
    num_valid_boxes: (optional) a Tensor of type `int32`. A 1-D tensor of shape
      [batch_size] representing the number of valid boxes to be considered for
      each image in the batch.  This parameter allows for ignoring zero
      paddings.
    masks: (optional) a [batch_size, num_anchors, q, mask_height, mask_width]
      float32 tensor containing box masks. `q` can be either number of classes
      or 1 depending on whether a separate mask is predicted per class.
    additional_fields: (optional) If not None, a dictionary that maps keys to
      tensors whose dimensions are [batch_size, num_anchors, ...].
    soft_nms_sigma: A scalar float representing the Soft NMS sigma parameter;
      See Bodla et al, https://arxiv.org/abs/1704.04503).  When
      `soft_nms_sigma=0.0` (which is default), we fall back to standard (hard)
      NMS.  Soft NMS is currently only supported when pad_to_max_output_size is
      False.
    scope: tf scope name.
    use_static_shapes: If true, the output nmsed boxes are padded to be of
      length `max_size_per_class` and it doesn't clip boxes to max_total_size.
      Defaults to false.
    use_partitioned_nms: If true, use partitioned version of
      non_max_suppression.
    parallel_iterations: (optional) number of batch items to process in
      parallel.
    use_class_agnostic_nms: If true, this uses class-agnostic non max
      suppression
    max_classes_per_detection: Maximum number of retained classes per detection
      box in class-agnostic NMS.
    use_dynamic_map_fn: If true, images in the batch will be processed within a
      dynamic loop. Otherwise, a static loop will be used if possible.
    use_combined_nms: If true, it uses tf.image.combined_non_max_suppression (
      multi-class version of NMS that operates on a batch).
      It greedily selects a subset of detection bounding boxes, pruning away
      boxes that have high IOU (intersection over union) overlap (> thresh) with
      already selected boxes. It operates independently for each batch.
      Within each batch, it operates independently for each class for which
      scores are provided (via the scores field of the input box_list),
      pruning boxes with score less than a provided threshold prior to applying
      NMS. This operation is performed on *all* batches and *all* classes
      in the batch, therefore any background classes should be removed prior to
      calling this function.
      Masks and additional fields are not supported.
      See argument checks in the code below for unsupported arguments.
    use_hard_nms: Enforce the usage of hard NMS.
    use_cpu_nms: Enforce NMS to run on CPU.

  Returns:
    'nmsed_boxes': A [batch_size, max_detections, 4] float32 tensor
      containing the non-max suppressed boxes.
    'nmsed_scores': A [batch_size, max_detections] float32 tensor containing
      the scores for the boxes.
    'nmsed_classes': A [batch_size, max_detections] float32 tensor
      containing the class for boxes.
    'nmsed_masks': (optional) a
      [batch_size, max_detections, mask_height, mask_width] float32 tensor
      containing masks for each selected box. This is set to None if input
      `masks` is None.
    'nmsed_additional_fields': (optional) a dictionary of
      [batch_size, max_detections, ...] float32 tensors corresponding to the
      tensors specified in the input `additional_fields`. This is not returned
      if input `additional_fields` is None.
    'num_detections': A [batch_size] int32 tensor indicating the number of
      valid detections per batch item. Only the top num_detections[i] entries in
      nms_boxes[i], nms_scores[i] and nms_class[i] are valid. The rest of the
      entries are zero paddings.

  Raises:
    ValueError: if `q` in boxes.shape is not 1 or not equal to number of
      classes as inferred from scores.shape.
  """
  if use_combined_nms:
    if change_coordinate_frame:
      raise ValueError(
          'change_coordinate_frame (normalizing coordinates'
          ' relative to clip_window) is not supported by combined_nms.')
    if num_valid_boxes is not None:
      raise ValueError('num_valid_boxes is not supported by combined_nms.')
    if masks is not None:
      raise ValueError('masks is not supported by combined_nms.')
    if soft_nms_sigma != 0.0:
      raise ValueError('Soft NMS is not supported by combined_nms.')
    if use_class_agnostic_nms:
      raise ValueError('class-agnostic NMS is not supported by combined_nms.')
    if clip_window is None:
      tf.logging.warning(
          'A default clip window of [0. 0. 1. 1.] will be applied for the '
          'boxes.')
    if additional_fields is not None:
      tf.logging.warning('additional_fields is not supported by combined_nms.')
    if parallel_iterations != 32:
      tf.logging.warning('Number of batch items to be processed in parallel is'
                         ' not configurable by combined_nms.')
    if max_classes_per_detection > 1:
      tf.logging.warning(
          'max_classes_per_detection is not configurable by combined_nms.')

    with tf.name_scope(scope, 'CombinedNonMaxSuppression'):
      (batch_nmsed_boxes, batch_nmsed_scores, batch_nmsed_classes,
       batch_num_detections) = tf.image.combined_non_max_suppression(
           boxes=boxes,
           scores=scores,
           max_output_size_per_class=max_size_per_class,
           max_total_size=max_total_size,
           iou_threshold=iou_thresh,
           score_threshold=score_thresh,
           clip_boxes=(True if clip_window is None else False),
           pad_per_class=use_static_shapes)
      if clip_window is not None:
        if clip_window.shape.ndims == 1:
          boxes_shape = boxes.shape
          batch_size = shape_utils.get_dim_as_int(boxes_shape[0])
          clip_window = tf.tile(clip_window[tf.newaxis, :], [batch_size, 1])
        batch_nmsed_boxes = _clip_boxes(batch_nmsed_boxes, clip_window)
      # Not supported by combined_non_max_suppression.
      batch_nmsed_masks = None
      # Not supported by combined_non_max_suppression.
      batch_nmsed_additional_fields = None
      return (batch_nmsed_boxes, batch_nmsed_scores, batch_nmsed_classes,
              batch_nmsed_masks, batch_nmsed_additional_fields,
              batch_num_detections)

  q = shape_utils.get_dim_as_int(boxes.shape[2])
  num_classes = shape_utils.get_dim_as_int(scores.shape[2])
  if q != 1 and q != num_classes:
    raise ValueError('third dimension of boxes must be either 1 or equal '
                     'to the third dimension of scores.')
  if change_coordinate_frame and clip_window is None:
    raise ValueError('if change_coordinate_frame is True, then a clip_window'
                     'must be specified.')
  original_masks = masks

  # Create ordered dictionary using the sorted keys from
  # additional fields to ensure getting the same key value assignment
  # in _single_image_nms_fn(). The dictionary is thus a sorted version of
  # additional_fields.
  if additional_fields is None:
    ordered_additional_fields = collections.OrderedDict()
  else:
    ordered_additional_fields = collections.OrderedDict(
        sorted(additional_fields.items(), key=lambda item: item[0]))

  with tf.name_scope(scope, 'BatchMultiClassNonMaxSuppression'):
    boxes_shape = boxes.shape
    batch_size = shape_utils.get_dim_as_int(boxes_shape[0])
    num_anchors = shape_utils.get_dim_as_int(boxes_shape[1])

    if batch_size is None:
      batch_size = tf.shape(boxes)[0]
    if num_anchors is None:
      num_anchors = tf.shape(boxes)[1]

    # If num valid boxes aren't provided, create one and mark all boxes as
    # valid.
    if num_valid_boxes is None:
      num_valid_boxes = tf.ones([batch_size], dtype=tf.int32) * num_anchors

    # If masks aren't provided, create dummy masks so we can only have one copy
    # of _single_image_nms_fn and discard the dummy masks after map_fn.
    if masks is None:
      masks_shape = tf.stack([batch_size, num_anchors, q, 1, 1])
      masks = tf.zeros(masks_shape)

    if clip_window is None:
      clip_window = tf.stack([
          tf.reduce_min(boxes[:, :, :, 0]),
          tf.reduce_min(boxes[:, :, :, 1]),
          tf.reduce_max(boxes[:, :, :, 2]),
          tf.reduce_max(boxes[:, :, :, 3])
      ])
    if clip_window.shape.ndims == 1:
      clip_window = tf.tile(tf.expand_dims(clip_window, 0), [batch_size, 1])

    def _single_image_nms_fn(args):
      """Runs NMS on a single image and returns padded output.

      Args:
        args: A list of tensors consisting of the following:
          per_image_boxes - A [num_anchors, q, 4] float32 tensor containing
            detections. If `q` is 1 then same boxes are used for all classes
            otherwise, if `q` is equal to number of classes, class-specific
            boxes are used.
          per_image_scores - A [num_anchors, num_classes] float32 tensor
            containing the scores for each of the `num_anchors` detections.
          per_image_masks - A [num_anchors, q, mask_height, mask_width] float32
            tensor containing box masks. `q` can be either number of classes
            or 1 depending on whether a separate mask is predicted per class.
          per_image_clip_window - A 1D float32 tensor of the form
            [ymin, xmin, ymax, xmax] representing the window to clip the boxes
            to.
          per_image_additional_fields - (optional) A variable number of float32
            tensors each with size [num_anchors, ...].
          per_image_num_valid_boxes - A tensor of type `int32`. A 1-D tensor of
            shape [batch_size] representing the number of valid boxes to be
            considered for each image in the batch.  This parameter allows for
            ignoring zero paddings.

      Returns:
        'nmsed_boxes': A [max_detections, 4] float32 tensor containing the
          non-max suppressed boxes.
        'nmsed_scores': A [max_detections] float32 tensor containing the scores
          for the boxes.
        'nmsed_classes': A [max_detections] float32 tensor containing the class
          for boxes.
        'nmsed_masks': (optional) a [max_detections, mask_height, mask_width]
          float32 tensor containing masks for each selected box. This is set to
          None if input `masks` is None.
        'nmsed_additional_fields':  (optional) A variable number of float32
          tensors each with size [max_detections, ...] corresponding to the
          input `per_image_additional_fields`.
        'num_detections': A [batch_size] int32 tensor indicating the number of
          valid detections per batch item. Only the top num_detections[i]
          entries in nms_boxes[i], nms_scores[i] and nms_class[i] are valid. The
          rest of the entries are zero paddings.
      """
      per_image_boxes = args[0]
      per_image_scores = args[1]
      per_image_masks = args[2]
      per_image_clip_window = args[3]
      # Make sure that the order of elements passed in args is aligned with
      # the iteration order of ordered_additional_fields
      per_image_additional_fields = {
          key: value
          for key, value in zip(ordered_additional_fields, args[4:-1])
      }
      per_image_num_valid_boxes = args[-1]
      if use_static_shapes:
        total_proposals = tf.shape(per_image_scores)
        per_image_scores = tf.where(
            tf.less(tf.range(total_proposals[0]), per_image_num_valid_boxes),
            per_image_scores,
            tf.fill(total_proposals, np.finfo('float32').min))
      else:
        per_image_boxes = tf.reshape(
            tf.slice(per_image_boxes, 3 * [0],
                     tf.stack([per_image_num_valid_boxes, -1, -1])), [-1, q, 4])
        per_image_scores = tf.reshape(
            tf.slice(per_image_scores, [0, 0],
                     tf.stack([per_image_num_valid_boxes, -1])),
            [-1, num_classes])
        per_image_masks = tf.reshape(
            tf.slice(per_image_masks, 4 * [0],
                     tf.stack([per_image_num_valid_boxes, -1, -1, -1])),
            [-1, q, shape_utils.get_dim_as_int(per_image_masks.shape[2]),
             shape_utils.get_dim_as_int(per_image_masks.shape[3])])
        if per_image_additional_fields is not None:
          for key, tensor in per_image_additional_fields.items():
            additional_field_shape = tensor.get_shape()
            additional_field_dim = len(additional_field_shape)
            per_image_additional_fields[key] = tf.reshape(
                tf.slice(
                    per_image_additional_fields[key],
                    additional_field_dim * [0],
                    tf.stack([per_image_num_valid_boxes] +
                             (additional_field_dim - 1) * [-1])), [-1] + [
                                 shape_utils.get_dim_as_int(dim)
                                 for dim in additional_field_shape[1:]
                             ])
      if use_class_agnostic_nms:
        nmsed_boxlist, num_valid_nms_boxes = class_agnostic_non_max_suppression(
            per_image_boxes,
            per_image_scores,
            score_thresh,
            iou_thresh,
            max_classes_per_detection,
            max_total_size,
            clip_window=per_image_clip_window,
            change_coordinate_frame=change_coordinate_frame,
            masks=per_image_masks,
            pad_to_max_output_size=use_static_shapes,
            use_partitioned_nms=use_partitioned_nms,
            additional_fields=per_image_additional_fields,
            soft_nms_sigma=soft_nms_sigma)
      else:
        nmsed_boxlist, num_valid_nms_boxes = multiclass_non_max_suppression(
            per_image_boxes,
            per_image_scores,
            score_thresh,
            iou_thresh,
            max_size_per_class,
            max_total_size,
            clip_window=per_image_clip_window,
            change_coordinate_frame=change_coordinate_frame,
            masks=per_image_masks,
            pad_to_max_output_size=use_static_shapes,
            use_partitioned_nms=use_partitioned_nms,
            additional_fields=per_image_additional_fields,
            soft_nms_sigma=soft_nms_sigma,
            use_hard_nms=use_hard_nms,
            use_cpu_nms=use_cpu_nms)

      if not use_static_shapes:
        nmsed_boxlist = box_list_ops.pad_or_clip_box_list(
            nmsed_boxlist, max_total_size)
      num_detections = num_valid_nms_boxes
      nmsed_boxes = nmsed_boxlist.get()
      nmsed_scores = nmsed_boxlist.get_field(fields.BoxListFields.scores)
      nmsed_classes = nmsed_boxlist.get_field(fields.BoxListFields.classes)
      nmsed_masks = nmsed_boxlist.get_field(fields.BoxListFields.masks)
      nmsed_additional_fields = []
      # Sorting is needed here to ensure that the values stored in
      # nmsed_additional_fields are always kept in the same order
      # across different execution runs.
      for key in sorted(per_image_additional_fields.keys()):
        nmsed_additional_fields.append(nmsed_boxlist.get_field(key))
      return ([nmsed_boxes, nmsed_scores, nmsed_classes, nmsed_masks] +
              nmsed_additional_fields + [num_detections])

    num_additional_fields = 0
    if ordered_additional_fields:
      num_additional_fields = len(ordered_additional_fields)
    num_nmsed_outputs = 4 + num_additional_fields

    if use_dynamic_map_fn:
      map_fn = tf.map_fn
    else:
      map_fn = shape_utils.static_or_dynamic_map_fn

    batch_outputs = map_fn(
        _single_image_nms_fn,
        elems=([boxes, scores, masks, clip_window] +
               list(ordered_additional_fields.values()) + [num_valid_boxes]),
        dtype=(num_nmsed_outputs * [tf.float32] + [tf.int32]),
        parallel_iterations=parallel_iterations)

    batch_nmsed_boxes = batch_outputs[0]
    batch_nmsed_scores = batch_outputs[1]
    batch_nmsed_classes = batch_outputs[2]
    batch_nmsed_masks = batch_outputs[3]
    batch_nmsed_values = batch_outputs[4:-1]

    batch_nmsed_additional_fields = {}
    if num_additional_fields > 0:
      # Sort the keys to ensure arranging elements in same order as
      # in _single_image_nms_fn.
      batch_nmsed_keys = list(ordered_additional_fields.keys())
      for i in range(len(batch_nmsed_keys)):
        batch_nmsed_additional_fields[
            batch_nmsed_keys[i]] = batch_nmsed_values[i]

    batch_num_detections = batch_outputs[-1]

    if original_masks is None:
      batch_nmsed_masks = None

    if not ordered_additional_fields:
      batch_nmsed_additional_fields = None

    return (batch_nmsed_boxes, batch_nmsed_scores, batch_nmsed_classes,
            batch_nmsed_masks, batch_nmsed_additional_fields,
            batch_num_detections)