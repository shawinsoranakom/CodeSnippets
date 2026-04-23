def _run_frcnn_head(self,
                      features,
                      rois,
                      gt_boxes,
                      gt_classes,
                      training,
                      model_outputs,
                      cascade_num,
                      regression_weights,
                      gt_outer_boxes=None):
    """Runs the frcnn head that does both class and box prediction.

    Args:
      features: `list` of features from the feature extractor.
      rois: `list` of current rois that will be used to predict bbox refinement
        and classes from.
      gt_boxes: a tensor with a shape of [batch_size, MAX_NUM_INSTANCES, 4].
        This tensor might have paddings with a negative value.
      gt_classes: [batch_size, MAX_INSTANCES] representing the groundtruth box
        classes. It is padded with -1s to indicate the invalid classes.
      training: `bool`, if model is training or being evaluated.
      model_outputs: `dict`, used for storing outputs used for eval and losses.
      cascade_num: `int`, the current frcnn layer in the cascade.
      regression_weights: `list`, weights used for l1 loss in bounding box
        regression.
      gt_outer_boxes: a tensor with a shape of [batch_size, MAX_NUM_INSTANCES,
        4]. This tensor might have paddings with a negative value. Default to
        None.

    Returns:
      class_outputs: Class predictions for rois.
      box_outputs: Box predictions for rois. These are formatted for the
        regression loss and need to be converted before being used as rois
        in the next stage.
      model_outputs: Updated dict with predictions used for losses and eval.
      matched_gt_boxes: If `is_training` is true, then these give the gt box
        location of its positive match.
      matched_gt_classes: If `is_training` is true, then these give the gt class
         of the predicted box.
      matched_gt_boxes: If `is_training` is true, then these give the box
        location of its positive match.
      matched_gt_outer_boxes: If `is_training` is true, then these give the
        outer box location of its positive match. Only exist if
        outer_boxes_scale is greater than 1.0.
      matched_gt_indices: If `is_training` is true, then gives the index of
        the positive box match. Used for mask prediction.
      rois: The sampled rois used for this layer.
    """
    # Only used during training.
    matched_gt_boxes, matched_gt_classes, matched_gt_indices = None, None, None
    if self.outer_boxes_scale > 1.0:
      matched_gt_outer_boxes = None

    if training and gt_boxes is not None:
      rois = tf.stop_gradient(rois)

      current_roi_sampler = self.roi_sampler[cascade_num]
      if self.outer_boxes_scale == 1.0:
        rois, matched_gt_boxes, matched_gt_classes, matched_gt_indices = (
            current_roi_sampler(rois, gt_boxes, gt_classes))
      else:
        (rois, matched_gt_boxes, matched_gt_outer_boxes, matched_gt_classes,
         matched_gt_indices) = current_roi_sampler(rois, gt_boxes, gt_classes,
                                                   gt_outer_boxes)
      # Create bounding box training targets.
      box_targets = box_ops.encode_boxes(
          matched_gt_boxes, rois, weights=regression_weights)
      # If the target is background, the box target is set to all 0s.
      box_targets = tf.where(
          tf.tile(
              tf.expand_dims(tf.equal(matched_gt_classes, 0), axis=-1),
              [1, 1, 4]), tf.zeros_like(box_targets), box_targets)
      model_outputs.update({
          'class_targets_{}'.format(cascade_num)
          if cascade_num else 'class_targets':
              matched_gt_classes,
          'box_targets_{}'.format(cascade_num)
          if cascade_num else 'box_targets':
              box_targets,
      })

    # Get roi features.
    roi_features = self.roi_aligner(features, rois)

    # Run frcnn head to get class and bbox predictions.
    current_detection_head = self.detection_head[cascade_num]
    class_outputs, box_outputs = current_detection_head(roi_features)

    model_outputs.update({
        'class_outputs_{}'.format(cascade_num)
        if cascade_num else 'class_outputs':
            class_outputs,
        'box_outputs_{}'.format(cascade_num) if cascade_num else 'box_outputs':
            box_outputs,
    })
    if self.outer_boxes_scale == 1.0:
      return (class_outputs, box_outputs, model_outputs, matched_gt_boxes,
              matched_gt_classes, matched_gt_indices, rois)
    else:
      return (class_outputs, box_outputs, model_outputs,
              (matched_gt_boxes, matched_gt_outer_boxes), matched_gt_classes,
              matched_gt_indices, rois)