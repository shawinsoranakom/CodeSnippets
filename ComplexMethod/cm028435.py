def build_outputs(self, inputs, mode):
    is_training = mode == mode_keys.TRAIN
    model_outputs = {}

    image = inputs['image']
    _, image_height, image_width, _ = image.get_shape().as_list()
    backbone_features = self._backbone_fn(image, is_training)
    fpn_features = self._fpn_fn(backbone_features, is_training)

    # rpn_centerness.
    if self._include_centerness:
      rpn_score_outputs, rpn_box_outputs, rpn_center_outputs = (
          self._rpn_head_fn(fpn_features, is_training))
      model_outputs.update({
          'rpn_center_outputs':
              tf.nest.map_structure(lambda x: tf.cast(x, tf.float32),
                                    rpn_center_outputs),
      })
      object_scores = rpn_center_outputs
    else:
      rpn_score_outputs, rpn_box_outputs = self._rpn_head_fn(
          fpn_features, is_training)
      object_scores = None
    model_outputs.update({
        'rpn_score_outputs':
            tf.nest.map_structure(lambda x: tf.cast(x, tf.float32),
                                  rpn_score_outputs),
        'rpn_box_outputs':
            tf.nest.map_structure(lambda x: tf.cast(x, tf.float32),
                                  rpn_box_outputs),
    })
    input_anchor = anchor.Anchor(self._params.architecture.min_level,
                                 self._params.architecture.max_level,
                                 self._params.anchor.num_scales,
                                 self._params.anchor.aspect_ratios,
                                 self._params.anchor.anchor_size,
                                 (image_height, image_width))
    rpn_rois, rpn_roi_scores = self._generate_rois_fn(
        rpn_box_outputs,
        rpn_score_outputs,
        input_anchor.multilevel_boxes,
        inputs['image_info'][:, 1, :],
        is_training,
        is_box_lrtb=self._include_centerness,
        object_scores=object_scores,
        )
    if (not self._include_frcnn_class and
        not self._include_frcnn_box and
        not self._include_mask):
      # if not is_training:
      # For direct RPN detection,
      # use dummy box_outputs = (dy,dx,dh,dw = 0,0,0,0)
      box_outputs = tf.zeros_like(rpn_rois)
      box_outputs = tf.concat([box_outputs, box_outputs], -1)
      boxes, scores, classes, valid_detections = self._generate_detections_fn(
          box_outputs, rpn_roi_scores, rpn_rois,
          inputs['image_info'][:, 1:2, :],
          is_single_fg_score=True,  # if no_background, no softmax is applied.
          keep_nms=True)
      model_outputs.update({
          'num_detections': valid_detections,
          'detection_boxes': boxes,
          'detection_classes': classes,
          'detection_scores': scores,
      })
      return model_outputs

    # ---- OLN-Proposal finishes here. ----

    if is_training:
      rpn_rois = tf.stop_gradient(rpn_rois)
      rpn_roi_scores = tf.stop_gradient(rpn_roi_scores)

      # Sample proposals.
      (rpn_rois, rpn_roi_scores, matched_gt_boxes, matched_gt_classes,
       matched_gt_indices) = (
           self._sample_rois_fn(rpn_rois, rpn_roi_scores, inputs['gt_boxes'],
                                inputs['gt_classes']))
      # Create bounding box training targets.
      box_targets = box_utils.encode_boxes(
          matched_gt_boxes, rpn_rois, weights=[10.0, 10.0, 5.0, 5.0])
      # If the target is background, the box target is set to all 0s.
      box_targets = tf.where(
          tf.tile(
              tf.expand_dims(tf.equal(matched_gt_classes, 0), axis=-1),
              [1, 1, 4]), tf.zeros_like(box_targets), box_targets)
      model_outputs.update({
          'class_targets': matched_gt_classes,
          'box_targets': box_targets,
      })
      # Create Box-IoU targets. {
      box_ious = box_utils.bbox_overlap(
          rpn_rois, inputs['gt_boxes'])
      matched_box_ious = tf.reduce_max(box_ious, 2)
      model_outputs.update({
          'box_iou_targets': matched_box_ious,})  # }

    roi_features = spatial_transform_ops.multilevel_crop_and_resize(
        fpn_features, rpn_rois, output_size=7)

    if not self._include_box_score:
      class_outputs, box_outputs = self._frcnn_head_fn(
          roi_features, is_training)
    else:
      class_outputs, box_outputs, score_outputs = self._frcnn_head_fn(
          roi_features, is_training)
      model_outputs.update({
          'box_score_outputs':
              tf.nest.map_structure(lambda x: tf.cast(x, tf.float32),
                                    score_outputs),})
    model_outputs.update({
        'class_outputs':
            tf.nest.map_structure(lambda x: tf.cast(x, tf.float32),
                                  class_outputs),
        'box_outputs':
            tf.nest.map_structure(lambda x: tf.cast(x, tf.float32),
                                  box_outputs),
    })

    # Add this output to train to make the checkpoint loadable in predict mode.
    # If we skip it in train mode, the heads will be out-of-order and checkpoint
    # loading will fail.
    if not self._include_frcnn_box:
      box_outputs = tf.zeros_like(box_outputs)  # dummy zeros.

    if self._include_box_score:
      score_outputs = tf.cast(tf.squeeze(score_outputs, -1),
                              rpn_roi_scores.dtype)

      # box-score = (rpn-centerness * box-iou)^(1/2)
      # TR: rpn_roi_scores: b,1000, score_outputs: b,512
      # TS: rpn_roi_scores: b,1000, score_outputs: b,1000
      box_scores = tf.pow(
          rpn_roi_scores * tf.sigmoid(score_outputs), 1/2.)

    if not self._include_frcnn_class:
      boxes, scores, classes, valid_detections = self._generate_detections_fn(
          box_outputs,
          box_scores,
          rpn_rois,
          inputs['image_info'][:, 1:2, :],
          is_single_fg_score=True,
          keep_nms=True,)
    else:
      boxes, scores, classes, valid_detections = self._generate_detections_fn(
          box_outputs, class_outputs, rpn_rois,
          inputs['image_info'][:, 1:2, :],
          keep_nms=True,)
    model_outputs.update({
        'num_detections': valid_detections,
        'detection_boxes': boxes,
        'detection_classes': classes,
        'detection_scores': scores,
    })

    # ---- OLN-Box finishes here. ----

    if not self._include_mask:
      return model_outputs

    if is_training:
      rpn_rois, classes, mask_targets = self._sample_masks_fn(
          rpn_rois, matched_gt_boxes, matched_gt_classes, matched_gt_indices,
          inputs['gt_masks'])
      mask_targets = tf.stop_gradient(mask_targets)

      classes = tf.cast(classes, dtype=tf.int32)

      model_outputs.update({
          'mask_targets': mask_targets,
          'sampled_class_targets': classes,
      })
    else:
      rpn_rois = boxes
      classes = tf.cast(classes, dtype=tf.int32)

    mask_roi_features = spatial_transform_ops.multilevel_crop_and_resize(
        fpn_features, rpn_rois, output_size=14)

    mask_outputs = self._mrcnn_head_fn(mask_roi_features, classes, is_training)

    if is_training:
      model_outputs.update({
          'mask_outputs':
              tf.nest.map_structure(lambda x: tf.cast(x, tf.float32),
                                    mask_outputs),
      })
    else:
      model_outputs.update({'detection_masks': tf.nn.sigmoid(mask_outputs)})

    return model_outputs