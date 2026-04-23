def assign(self,
             anchors,
             groundtruth_boxes,
             groundtruth_labels=None,
             groundtruth_weights=None,
             **params):
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
      groundtruth_labels:  a tensor of shape [M, d_1, ... d_k] with labels for
        each of the ground_truth boxes. The subshape [d_1, ... d_k] can be empty
        (corresponding to scalar inputs).  When set to None, groundtruth_labels
        assumes a binary problem where all ground_truth boxes get a positive
        label (of 1).
      groundtruth_weights: a float tensor of shape [M] indicating the weight to
        assign to all anchors match to a particular groundtruth box. The weights
        must be in [0., 1.]. If None, all weights are set to 1.
      **params: Additional keyword arguments for specific implementations of the
        Matcher.

    Returns:
      cls_targets: a float32 tensor with shape [num_anchors, d_1, d_2 ... d_k],
        where the subshape [d_1, ..., d_k] is compatible with groundtruth_labels
        which has shape [num_gt_boxes, d_1, d_2, ... d_k].
      cls_weights: a float32 tensor with shape [num_anchors]
      reg_targets: a float32 tensor with shape [num_anchors, box_code_dimension]
      reg_weights: a float32 tensor with shape [num_anchors]
      match: a matcher.Match object encoding the match between anchors and
        groundtruth boxes, with rows corresponding to groundtruth boxes
        and columns corresponding to anchors.
      matched_gt_boxlist: a BoxList object with data of float32 tensor with
        shape [num_anchors, box_dimension] which encodes the coordinates of the
        matched groundtruth boxes.
      matched_anchors_mask: a Bool tensor with shape [num_anchors] which
        indicates whether an anchor is matched or not.
      center_matched_gt_boxlist: a BoxList object with data of float32 tensor
        with shape [num_anchors, box_dimension] which encodes the coordinates of
        the groundtruth boxes matched for centerness target assignment.
      center_matched_anchors_mask: a Boolean tensor with shape [num_anchors]
        which indicates whether an anchor is matched or not for centerness
        target assignment.
      matched_ious: a float32 tensor with shape [num_anchors] which encodes the
        ious between each anchor and the matched groundtruth boxes.

    Raises:
      ValueError: if anchors or groundtruth_boxes are not of type
        box_list.BoxList
    """
    if not isinstance(anchors, box_list.BoxList):
      raise ValueError('anchors must be an BoxList')
    if not isinstance(groundtruth_boxes, box_list.BoxList):
      raise ValueError('groundtruth_boxes must be an BoxList')

    if groundtruth_labels is None:
      groundtruth_labels = tf.ones(
          tf.expand_dims(groundtruth_boxes.num_boxes(), 0))
      groundtruth_labels = tf.expand_dims(groundtruth_labels, -1)
    unmatched_shape_assert = shape_utils.assert_shape_equal(
        shape_utils.combined_static_and_dynamic_shape(groundtruth_labels)[1:],
        shape_utils.combined_static_and_dynamic_shape(
            self._unmatched_cls_target))
    labels_and_box_shapes_assert = shape_utils.assert_shape_equal(
        shape_utils.combined_static_and_dynamic_shape(groundtruth_labels)[:1],
        shape_utils.combined_static_and_dynamic_shape(
            groundtruth_boxes.get())[:1])

    if groundtruth_weights is None:
      num_gt_boxes = groundtruth_boxes.num_boxes_static()
      if not num_gt_boxes:
        num_gt_boxes = groundtruth_boxes.num_boxes()
      groundtruth_weights = tf.ones([num_gt_boxes], dtype=tf.float32)
    with tf.control_dependencies(
        [unmatched_shape_assert, labels_and_box_shapes_assert]):
      match_quality_matrix = self._similarity_calc(
          groundtruth_boxes.get(), anchors.get())
      match = self._matcher.match(match_quality_matrix, **params)
      reg_targets, matched_gt_boxlist, matched_anchors_mask = (
          self._create_regression_targets(anchors,
                                          groundtruth_boxes,
                                          match))
      cls_targets = self._create_classification_targets(groundtruth_labels,
                                                        match)
      reg_weights = self._create_regression_weights(match, groundtruth_weights)
      cls_weights = self._create_classification_weights(match,
                                                        groundtruth_weights)
      # Match for creation of centerness regression targets.
      if self._center_matcher is not None:
        center_match = self._center_matcher.match(
            match_quality_matrix, **params)
        center_matched_gt_boxes = center_match.gather_based_on_match(
            groundtruth_boxes.get(),
            unmatched_value=tf.zeros(4),
            ignored_value=tf.zeros(4))
        center_matched_gt_boxlist = box_list.BoxList(center_matched_gt_boxes)
        center_matched_anchors_mask = center_match.matched_column_indicator()

    num_anchors = anchors.num_boxes_static()
    if num_anchors is not None:
      reg_targets = self._reset_target_shape(reg_targets, num_anchors)
      cls_targets = self._reset_target_shape(cls_targets, num_anchors)
      reg_weights = self._reset_target_shape(reg_weights, num_anchors)
      cls_weights = self._reset_target_shape(cls_weights, num_anchors)

    if self._center_matcher is not None:
      matched_ious = tf.reduce_max(match_quality_matrix, 0)
      return (cls_targets, cls_weights, reg_targets, reg_weights, match,
              matched_gt_boxlist, matched_anchors_mask,
              center_matched_gt_boxlist, center_matched_anchors_mask,
              matched_ious)
    else:
      return (cls_targets, cls_weights, reg_targets, reg_weights, match)