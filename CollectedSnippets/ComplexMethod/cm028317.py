def postprocess(self, prediction_dict, true_image_shapes, **params):
    """Produces boxes given a prediction dict returned by predict().

    Although predict returns a list of tensors, only the last tensor in
    each list is used for making box predictions.

    Args:
      prediction_dict: a dictionary holding predicted tensors from "predict"
        function.
      true_image_shapes: int32 tensor of shape [batch, 3] where each row is of
        the form [height, width, channels] indicating the shapes of true images
        in the resized images, as resized images can be padded with zeros.
      **params: Currently ignored.

    Returns:
      detections: a dictionary containing the following fields
        detection_boxes - A tensor of shape [batch, max_detections, 4]
          holding the predicted boxes.
        detection_boxes_strided: A tensor of shape [batch_size, num_detections,
          4] holding the predicted boxes in absolute coordinates of the
          feature extractor's final layer output.
        detection_scores: A tensor of shape [batch, max_detections] holding
          the predicted score for each box.
        detection_multiclass_scores: A tensor of shape [batch, max_detection,
          num_classes] holding multiclass score for each box.
        detection_classes: An integer tensor of shape [batch, max_detections]
          containing the detected class for each box.
        num_detections: An integer tensor of shape [batch] containing the
          number of detected boxes for each sample in the batch.
        detection_keypoints: (Optional) A float tensor of shape [batch,
          max_detections, num_keypoints, 2] with normalized keypoints. Any
          invalid keypoints have their coordinates and scores set to 0.0.
        detection_keypoint_scores: (Optional) A float tensor of shape [batch,
          max_detection, num_keypoints] with scores for each keypoint.
        detection_masks: (Optional) A uint8 tensor of shape [batch,
          max_detections, mask_height, mask_width] with masks for each
          detection. Background is specified with 0, and foreground is specified
          with positive integers (1 for standard instance segmentation mask, and
          1-indexed parts for DensePose task).
        detection_surface_coords: (Optional) A float32 tensor of shape [batch,
          max_detection, mask_height, mask_width, 2] with DensePose surface
          coordinates, in (v, u) format.
        detection_embeddings: (Optional) A float tensor of shape [batch,
          max_detections, reid_embed_size] containing object embeddings.
    """
    object_center_prob = tf.nn.sigmoid(prediction_dict[OBJECT_CENTER][-1])

    if true_image_shapes is None:
      # If true_image_shapes is not provided, we assume the whole image is valid
      # and infer the true_image_shapes from the object_center_prob shape.
      batch_size, strided_height, strided_width, _ = _get_shape(
          object_center_prob, 4)
      true_image_shapes = tf.stack(
          [strided_height * self._stride, strided_width * self._stride,
           tf.constant(len(self._feature_extractor._channel_means))])   # pylint: disable=protected-access
      true_image_shapes = tf.stack([true_image_shapes] * batch_size, axis=0)
    else:
      # Mask object centers by true_image_shape. [batch, h, w, 1]
      object_center_mask = mask_from_true_image_shape(
          _get_shape(object_center_prob, 4), true_image_shapes)
      object_center_prob *= object_center_mask

    # Get x, y and channel indices corresponding to the top indices in the class
    # center predictions.
    detection_scores, y_indices, x_indices, channel_indices = (
        top_k_feature_map_locations(
            object_center_prob,
            max_pool_kernel_size=self._center_params.peak_max_pool_kernel_size,
            k=self._center_params.max_box_predictions))
    multiclass_scores = tf.gather_nd(
        object_center_prob, tf.stack([y_indices, x_indices], -1), batch_dims=1)
    num_detections = tf.reduce_sum(
        tf.cast(detection_scores > 0, tf.int32), axis=1)
    postprocess_dict = {
        fields.DetectionResultFields.detection_scores: detection_scores,
        fields.DetectionResultFields.detection_multiclass_scores:
            multiclass_scores,
        fields.DetectionResultFields.detection_classes: channel_indices,
        fields.DetectionResultFields.num_detections: num_detections,
    }

    if self._output_prediction_dict:
      postprocess_dict.update(prediction_dict)
      postprocess_dict['true_image_shapes'] = true_image_shapes

    boxes_strided = None
    if self._od_params:
      boxes_strided = (
          prediction_tensors_to_boxes(y_indices, x_indices,
                                      prediction_dict[BOX_SCALE][-1],
                                      prediction_dict[BOX_OFFSET][-1]))

      boxes = convert_strided_predictions_to_normalized_boxes(
          boxes_strided, self._stride, true_image_shapes)

      postprocess_dict.update({
          fields.DetectionResultFields.detection_boxes: boxes,
          'detection_boxes_strided': boxes_strided,
      })

    if self._kp_params_dict:
      # If the model is trained to predict only one class of object and its
      # keypoint, we fall back to a simpler postprocessing function which uses
      # the ops that are supported by tf.lite on GPU.
      clip_keypoints = self._should_clip_keypoints()
      if len(self._kp_params_dict) == 1 and self._num_classes == 1:
        task_name, kp_params = next(iter(self._kp_params_dict.items()))
        keypoint_depths = None
        if kp_params.argmax_postprocessing:
          keypoints, keypoint_scores = (
              prediction_to_keypoints_argmax(
                  prediction_dict,
                  object_y_indices=y_indices,
                  object_x_indices=x_indices,
                  boxes=boxes_strided,
                  task_name=task_name,
                  kp_params=kp_params))
        else:
          (keypoints, keypoint_scores,
           keypoint_depths) = self._postprocess_keypoints_single_class(
               prediction_dict, channel_indices, y_indices, x_indices,
               boxes_strided, num_detections)
        keypoints, keypoint_scores = (
            convert_strided_predictions_to_normalized_keypoints(
                keypoints, keypoint_scores, self._stride, true_image_shapes,
                clip_out_of_frame_keypoints=clip_keypoints))
        if keypoint_depths is not None:
          postprocess_dict.update({
              fields.DetectionResultFields.detection_keypoint_depths:
                  keypoint_depths
          })
      else:
        # Multi-class keypoint estimation task does not support depth
        # estimation.
        assert all([
            not kp_dict.predict_depth
            for kp_dict in self._kp_params_dict.values()
        ])
        keypoints, keypoint_scores = self._postprocess_keypoints_multi_class(
            prediction_dict, channel_indices, y_indices, x_indices,
            boxes_strided, num_detections)
        keypoints, keypoint_scores = (
            convert_strided_predictions_to_normalized_keypoints(
                keypoints, keypoint_scores, self._stride, true_image_shapes,
                clip_out_of_frame_keypoints=clip_keypoints))

      postprocess_dict.update({
          fields.DetectionResultFields.detection_keypoints: keypoints,
          fields.DetectionResultFields.detection_keypoint_scores:
              keypoint_scores
      })
      if self._od_params is None:
        # Still output the box prediction by enclosing the keypoints for
        # evaluation purpose.
        boxes = keypoint_ops.keypoints_to_enclosing_bounding_boxes(
            keypoints, keypoints_axis=2)
        postprocess_dict.update({
            fields.DetectionResultFields.detection_boxes: boxes,
        })

    if self._mask_params:
      masks = tf.nn.sigmoid(prediction_dict[SEGMENTATION_HEATMAP][-1])
      densepose_part_heatmap, densepose_surface_coords = None, None
      densepose_class_index = 0
      if self._densepose_params:
        densepose_part_heatmap = prediction_dict[DENSEPOSE_HEATMAP][-1]
        densepose_surface_coords = prediction_dict[DENSEPOSE_REGRESSION][-1]
        densepose_class_index = self._densepose_params.class_id
      instance_masks, surface_coords = (
          convert_strided_predictions_to_instance_masks(
              boxes, channel_indices, masks, true_image_shapes,
              densepose_part_heatmap, densepose_surface_coords,
              stride=self._stride, mask_height=self._mask_params.mask_height,
              mask_width=self._mask_params.mask_width,
              score_threshold=self._mask_params.score_threshold,
              densepose_class_index=densepose_class_index))
      postprocess_dict[
          fields.DetectionResultFields.detection_masks] = instance_masks
      if self._densepose_params:
        postprocess_dict[
            fields.DetectionResultFields.detection_surface_coords] = (
                surface_coords)

    if self._track_params:
      embeddings = self._postprocess_embeddings(prediction_dict,
                                                y_indices, x_indices)
      postprocess_dict.update({
          fields.DetectionResultFields.detection_embeddings: embeddings
      })

    if self._temporal_offset_params:
      offsets = prediction_tensors_to_temporal_offsets(
          y_indices, x_indices,
          prediction_dict[TEMPORAL_OFFSET][-1])
      postprocess_dict[fields.DetectionResultFields.detection_offsets] = offsets

    if self._non_max_suppression_fn:
      boxes = tf.expand_dims(
          postprocess_dict.pop(fields.DetectionResultFields.detection_boxes),
          axis=-2)
      multiclass_scores = postprocess_dict[
          fields.DetectionResultFields.detection_multiclass_scores]
      num_classes = tf.shape(multiclass_scores)[2]
      class_mask = tf.cast(
          tf.one_hot(
              postprocess_dict[fields.DetectionResultFields.detection_classes],
              depth=num_classes), tf.bool)
      # Surpress the scores of those unselected classes to be zeros. Otherwise,
      # the downstream NMS ops might be confused and introduce issues.
      multiclass_scores = tf.where(
          class_mask, multiclass_scores, tf.zeros_like(multiclass_scores))
      num_valid_boxes = postprocess_dict.pop(
          fields.DetectionResultFields.num_detections)
      # Remove scores and classes as NMS will compute these form multiclass
      # scores.
      postprocess_dict.pop(fields.DetectionResultFields.detection_scores)
      postprocess_dict.pop(fields.DetectionResultFields.detection_classes)
      (nmsed_boxes, nmsed_scores, nmsed_classes, _, nmsed_additional_fields,
       num_detections) = self._non_max_suppression_fn(
           boxes,
           multiclass_scores,
           additional_fields=postprocess_dict,
           num_valid_boxes=num_valid_boxes)
      postprocess_dict = nmsed_additional_fields
      postprocess_dict[
          fields.DetectionResultFields.detection_boxes] = nmsed_boxes
      postprocess_dict[
          fields.DetectionResultFields.detection_scores] = nmsed_scores
      postprocess_dict[
          fields.DetectionResultFields.detection_classes] = nmsed_classes
      postprocess_dict[
          fields.DetectionResultFields.num_detections] = num_detections
      postprocess_dict.update(nmsed_additional_fields)

    # Perform the rescoring once the NMS is applied to make sure the rescored
    # scores won't be washed out by the NMS function.
    if self._kp_params_dict:
      channel_indices = postprocess_dict[
          fields.DetectionResultFields.detection_classes]
      detection_scores = postprocess_dict[
          fields.DetectionResultFields.detection_scores]
      keypoint_scores = postprocess_dict[
          fields.DetectionResultFields.detection_keypoint_scores]
      # Update instance scores based on keypoints.
      scores = self._rescore_instances(
          channel_indices, detection_scores, keypoint_scores)
      postprocess_dict.update({
          fields.DetectionResultFields.detection_scores: scores,
      })
    return postprocess_dict