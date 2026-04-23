def _assign_targets(self,
                      groundtruth_boxes_list,
                      groundtruth_classes_list,
                      groundtruth_keypoints_list=None,
                      groundtruth_weights_list=None,
                      groundtruth_confidences_list=None):
    """Assign groundtruth targets.

    Adds a background class to each one-hot encoding of groundtruth classes
    and uses target assigner to obtain regression and classification targets.

    Args:
      groundtruth_boxes_list: a list of 2-D tensors of shape [num_boxes, 4]
        containing coordinates of the groundtruth boxes.
          Groundtruth boxes are provided in [y_min, x_min, y_max, x_max]
          format and assumed to be normalized and clipped
          relative to the image window with y_min <= y_max and x_min <= x_max.
      groundtruth_classes_list: a list of 2-D one-hot (or k-hot) tensors of
        shape [num_boxes, num_classes] containing the class targets with the 0th
        index assumed to map to the first non-background class.
      groundtruth_keypoints_list: (optional) a list of 3-D tensors of shape
        [num_boxes, num_keypoints, 2]
      groundtruth_weights_list: A list of 1-D tf.float32 tensors of shape
        [num_boxes] containing weights for groundtruth boxes.
      groundtruth_confidences_list: A list of 2-D tf.float32 tensors of shape
        [num_boxes, num_classes] containing class confidences for
        groundtruth boxes.

    Returns:
      batch_cls_targets: a tensor with shape [batch_size, num_anchors,
        num_classes],
      batch_cls_weights: a tensor with shape [batch_size, num_anchors],
      batch_reg_targets: a tensor with shape [batch_size, num_anchors,
        box_code_dimension]
      batch_reg_weights: a tensor with shape [batch_size, num_anchors],
      match: an int32 tensor of shape [batch_size, num_anchors], containing
        result of anchor groundtruth matching. Each position in the tensor
        indicates an anchor and holds the following meaning:
        (1) if match[x, i] >= 0, anchor i is matched with groundtruth
            match[x, i].
        (2) if match[x, i]=-1, anchor i is marked to be background .
        (3) if match[x, i]=-2, anchor i is ignored since it is not background
            and does not have sufficient overlap to call it a foreground.
    """
    groundtruth_boxlists = [
        box_list.BoxList(boxes) for boxes in groundtruth_boxes_list
    ]
    train_using_confidences = (self._is_training and
                               self._use_confidences_as_targets)
    if self._add_background_class:
      groundtruth_classes_with_background_list = [
          tf.pad(one_hot_encoding, [[0, 0], [1, 0]], mode='CONSTANT')
          for one_hot_encoding in groundtruth_classes_list
      ]
      if train_using_confidences:
        groundtruth_confidences_with_background_list = [
            tf.pad(groundtruth_confidences, [[0, 0], [1, 0]], mode='CONSTANT')
            for groundtruth_confidences in groundtruth_confidences_list
        ]
    else:
      groundtruth_classes_with_background_list = groundtruth_classes_list

    if groundtruth_keypoints_list is not None:
      for boxlist, keypoints in zip(
          groundtruth_boxlists, groundtruth_keypoints_list):
        boxlist.add_field(fields.BoxListFields.keypoints, keypoints)
    if train_using_confidences:
      return target_assigner.batch_assign_confidences(
          self._target_assigner,
          self.anchors,
          groundtruth_boxlists,
          groundtruth_confidences_with_background_list,
          groundtruth_weights_list,
          self._unmatched_class_label,
          self._add_background_class,
          self._implicit_example_weight)
    else:
      return target_assigner.batch_assign_targets(
          self._target_assigner,
          self.anchors,
          groundtruth_boxlists,
          groundtruth_classes_with_background_list,
          self._unmatched_class_label,
          groundtruth_weights_list)