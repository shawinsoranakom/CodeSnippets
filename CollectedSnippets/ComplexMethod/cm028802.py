def _call_box_outputs(
      self,
      images: tf.Tensor,
      image_shape: tf.Tensor,
      anchor_boxes: Optional[Mapping[str, tf.Tensor]] = None,
      gt_boxes: Optional[tf.Tensor] = None,
      gt_classes: Optional[tf.Tensor] = None,
      training: Optional[bool] = None,
      gt_outer_boxes: Optional[tf.Tensor] = None,
  ) -> Tuple[Mapping[str, Any], Mapping[str, Any]]:
    """Implementation of the Faster-RCNN logic for boxes."""
    model_outputs = {}

    # Feature extraction.
    (backbone_features,
     decoder_features) = self._get_backbone_and_decoder_features(images)

    # Region proposal network.
    rpn_scores, rpn_boxes = self.rpn_head(decoder_features)

    model_outputs.update({
        'backbone_features': backbone_features,
        'decoder_features': decoder_features,
        'rpn_boxes': rpn_boxes,
        'rpn_scores': rpn_scores
    })

    # Generate anchor boxes for this batch if not provided.
    if anchor_boxes is None:
      _, image_height, image_width, _ = images.get_shape().as_list()
      anchor_boxes = anchor.Anchor(
          min_level=self._config_dict['min_level'],
          max_level=self._config_dict['max_level'],
          num_scales=self._config_dict['num_scales'],
          aspect_ratios=self._config_dict['aspect_ratios'],
          anchor_size=self._config_dict['anchor_size'],
          image_size=(image_height, image_width)).multilevel_boxes
      for l in anchor_boxes:
        anchor_boxes[l] = tf.tile(
            tf.expand_dims(anchor_boxes[l], axis=0),
            [tf.shape(images)[0], 1, 1, 1])

    # Generate RoIs.
    current_rois, _ = self.roi_generator(rpn_boxes, rpn_scores, anchor_boxes,
                                         image_shape, training)

    next_rois = current_rois
    all_class_outputs = []
    for cascade_num in range(len(self.roi_sampler)):
      # In cascade RCNN we want the higher layers to have different regression
      # weights as the predicted deltas become smaller and smaller.
      regression_weights = self._cascade_layer_to_weights[cascade_num]
      current_rois = next_rois

      if self.outer_boxes_scale == 1.0:
        (class_outputs, box_outputs, model_outputs, matched_gt_boxes,
         matched_gt_classes, matched_gt_indices,
         current_rois) = self._run_frcnn_head(
             features=decoder_features,
             rois=current_rois,
             gt_boxes=gt_boxes,
             gt_classes=gt_classes,
             training=training,
             model_outputs=model_outputs,
             cascade_num=cascade_num,
             regression_weights=regression_weights)
      else:
        (class_outputs, box_outputs, model_outputs,
         (matched_gt_boxes, matched_gt_outer_boxes), matched_gt_classes,
         matched_gt_indices, current_rois) = self._run_frcnn_head(
             features=decoder_features,
             rois=current_rois,
             gt_boxes=gt_boxes,
             gt_outer_boxes=gt_outer_boxes,
             gt_classes=gt_classes,
             training=training,
             model_outputs=model_outputs,
             cascade_num=cascade_num,
             regression_weights=regression_weights)
      all_class_outputs.append(class_outputs)

      # Generate ROIs for the next cascade head if there is any.
      if cascade_num < len(self.roi_sampler) - 1:
        next_rois = box_ops.decode_boxes(
            tf.cast(box_outputs, tf.float32),
            current_rois,
            weights=regression_weights)
        next_rois = box_ops.clip_boxes(next_rois,
                                       tf.expand_dims(image_shape, axis=1))

    if not training:
      if self._config_dict['cascade_class_ensemble']:
        class_outputs = tf.add_n(all_class_outputs) / len(all_class_outputs)

      detections = self.detection_generator(
          box_outputs,
          class_outputs,
          current_rois,
          image_shape,
          regression_weights,
          bbox_per_class=(not self._config_dict['class_agnostic_bbox_pred']))
      model_outputs.update({
          'cls_outputs': class_outputs,
          'box_outputs': box_outputs,
      })
      if self.detection_generator.get_config()['apply_nms']:
        model_outputs.update({
            'detection_boxes': detections['detection_boxes'],
            'detection_scores': detections['detection_scores'],
            'detection_classes': detections['detection_classes'],
            'num_detections': detections['num_detections']
        })
        if self.outer_boxes_scale > 1.0:
          detection_outer_boxes = box_ops.compute_outer_boxes(
              detections['detection_boxes'],
              tf.expand_dims(image_shape, axis=1), self.outer_boxes_scale)
          model_outputs['detection_outer_boxes'] = detection_outer_boxes
      else:
        model_outputs.update({
            'decoded_boxes': detections['decoded_boxes'],
            'decoded_box_scores': detections['decoded_box_scores']
        })

    intermediate_outputs = {
        'matched_gt_boxes': matched_gt_boxes,
        'matched_gt_indices': matched_gt_indices,
        'matched_gt_classes': matched_gt_classes,
        'current_rois': current_rois,
    }
    if self.outer_boxes_scale > 1.0:
      intermediate_outputs['matched_gt_outer_boxes'] = matched_gt_outer_boxes
    return (model_outputs, intermediate_outputs)