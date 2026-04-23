def assign(self,
             anchors,
             groundtruth_boxes,
             groundtruth_labels=None,
             unmatched_class_label=None,
             groundtruth_weights=None):
    """Assign classification and regression targets to each anchor.

    For a given set of anchors and groundtruth detections, match anchors
    to groundtruth_boxes and assign classification and regression targets to
    each anchor as well as weights based on the resulting match (specifying,
    e.g., which anchors should not contribute to training loss).

    Anchors that are not matched to anything are given a classification target
    of self._unmatched_cls_target which can be specified via the constructor.

    Args:
      anchors: a BoxList representing N anchors
      groundtruth_boxes: a BoxList representing M groundtruth boxes
      groundtruth_labels:  a tensor of shape [M, d_1, ... d_k]
        with labels for each of the ground_truth boxes. The subshape
        [d_1, ... d_k] can be empty (corresponding to scalar inputs).  When set
        to None, groundtruth_labels assumes a binary problem where all
        ground_truth boxes get a positive label (of 1).
      unmatched_class_label: a float32 tensor with shape [d_1, d_2, ..., d_k]
        which is consistent with the classification target for each
        anchor (and can be empty for scalar targets).  This shape must thus be
        compatible with the groundtruth labels that are passed to the "assign"
        function (which have shape [num_gt_boxes, d_1, d_2, ..., d_k]).
        If set to None, unmatched_cls_target is set to be [0] for each anchor.
      groundtruth_weights: a float tensor of shape [M] indicating the weight to
        assign to all anchors match to a particular groundtruth box. The weights
        must be in [0., 1.]. If None, all weights are set to 1. Generally no
        groundtruth boxes with zero weight match to any anchors as matchers are
        aware of groundtruth weights. Additionally, `cls_weights` and
        `reg_weights` are calculated using groundtruth weights as an added
        safety.

    Returns:
      cls_targets: a float32 tensor with shape [num_anchors, d_1, d_2 ... d_k],
        where the subshape [d_1, ..., d_k] is compatible with groundtruth_labels
        which has shape [num_gt_boxes, d_1, d_2, ... d_k].
      cls_weights: a float32 tensor with shape [num_anchors, d_1, d_2 ... d_k],
        representing weights for each element in cls_targets.
      reg_targets: a float32 tensor with shape [num_anchors, box_code_dimension]
      reg_weights: a float32 tensor with shape [num_anchors]
      match: an int32 tensor of shape [num_anchors] containing result of anchor
        groundtruth matching. Each position in the tensor indicates an anchor
        and holds the following meaning:
        (1) if match[i] >= 0, anchor i is matched with groundtruth match[i].
        (2) if match[i]=-1, anchor i is marked to be background .
        (3) if match[i]=-2, anchor i is ignored since it is not background and
            does not have sufficient overlap to call it a foreground.

    Raises:
      ValueError: if anchors or groundtruth_boxes are not of type
        box_list.BoxList
    """
    if not isinstance(anchors, box_list.BoxList):
      raise ValueError('anchors must be an BoxList')
    if not isinstance(groundtruth_boxes, box_list.BoxList):
      raise ValueError('groundtruth_boxes must be an BoxList')

    if unmatched_class_label is None:
      unmatched_class_label = tf.constant([0], tf.float32)

    if groundtruth_labels is None:
      groundtruth_labels = tf.ones(tf.expand_dims(groundtruth_boxes.num_boxes(),
                                                  0))
      groundtruth_labels = tf.expand_dims(groundtruth_labels, -1)

    unmatched_shape_assert = shape_utils.assert_shape_equal(
        shape_utils.combined_static_and_dynamic_shape(groundtruth_labels)[1:],
        shape_utils.combined_static_and_dynamic_shape(unmatched_class_label))
    labels_and_box_shapes_assert = shape_utils.assert_shape_equal(
        shape_utils.combined_static_and_dynamic_shape(
            groundtruth_labels)[:1],
        shape_utils.combined_static_and_dynamic_shape(
            groundtruth_boxes.get())[:1])

    if groundtruth_weights is None:
      num_gt_boxes = groundtruth_boxes.num_boxes_static()
      if not num_gt_boxes:
        num_gt_boxes = groundtruth_boxes.num_boxes()
      groundtruth_weights = tf.ones([num_gt_boxes], dtype=tf.float32)

    # set scores on the gt boxes
    scores = 1 - groundtruth_labels[:, 0]
    groundtruth_boxes.add_field(fields.BoxListFields.scores, scores)

    with tf.control_dependencies(
        [unmatched_shape_assert, labels_and_box_shapes_assert]):
      match_quality_matrix = self._similarity_calc.compare(groundtruth_boxes,
                                                           anchors)
      match = self._matcher.match(match_quality_matrix,
                                  valid_rows=tf.greater(groundtruth_weights, 0))
      reg_targets = self._create_regression_targets(anchors,
                                                    groundtruth_boxes,
                                                    match)
      cls_targets = self._create_classification_targets(groundtruth_labels,
                                                        unmatched_class_label,
                                                        match)
      reg_weights = self._create_regression_weights(match, groundtruth_weights)

      cls_weights = self._create_classification_weights(match,
                                                        groundtruth_weights)
      # convert cls_weights from per-anchor to per-class.
      class_label_shape = tf.shape(cls_targets)[1:]
      weights_shape = tf.shape(cls_weights)
      weights_multiple = tf.concat(
          [tf.ones_like(weights_shape), class_label_shape],
          axis=0)
      for _ in range(len(cls_targets.get_shape()[1:])):
        cls_weights = tf.expand_dims(cls_weights, -1)
      cls_weights = tf.tile(cls_weights, weights_multiple)

    num_anchors = anchors.num_boxes_static()
    if num_anchors is not None:
      reg_targets = self._reset_target_shape(reg_targets, num_anchors)
      cls_targets = self._reset_target_shape(cls_targets, num_anchors)
      reg_weights = self._reset_target_shape(reg_weights, num_anchors)
      cls_weights = self._reset_target_shape(cls_weights, num_anchors)

    return (cls_targets, cls_weights, reg_targets, reg_weights,
            match.match_results)