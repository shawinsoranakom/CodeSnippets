def loss(
      self, prediction_dict, true_image_shapes, scope=None,
      maximum_normalized_coordinate=1.1):
    """Computes scalar loss tensors with respect to provided groundtruth.

    This function implements the various CenterNet losses.

    Args:
      prediction_dict: a dictionary holding predicted tensors returned by
        "predict" function.
      true_image_shapes: int32 tensor of shape [batch, 3] where each row is of
        the form [height, width, channels] indicating the shapes of true images
        in the resized images, as resized images can be padded with zeros.
      scope: Optional scope name.
      maximum_normalized_coordinate: Maximum coordinate value to be considered
        as normalized, default to 1.1. This is used to check bounds during
        converting normalized coordinates to absolute coordinates.

    Returns:
      A dictionary mapping the keys [
        'Loss/object_center',
        'Loss/box/scale',  (optional)
        'Loss/box/offset', (optional)
        'Loss/$TASK_NAME/keypoint/heatmap', (optional)
        'Loss/$TASK_NAME/keypoint/offset', (optional)
        'Loss/$TASK_NAME/keypoint/regression', (optional)
        'Loss/segmentation/heatmap', (optional)
        'Loss/densepose/heatmap', (optional)
        'Loss/densepose/regression', (optional)
        'Loss/track/reid'] (optional)
        'Loss/track/offset'] (optional)
        scalar tensors corresponding to the losses for different tasks. Note the
        $TASK_NAME is provided by the KeypointEstimation namedtuple used to
        differentiate between different keypoint tasks.
    """

    _, input_height, input_width, _ = _get_shape(
        prediction_dict['preprocessed_inputs'], 4)

    output_height, output_width = (tf.maximum(input_height // self._stride, 1),
                                   tf.maximum(input_width // self._stride, 1))

    # TODO(vighneshb) Explore whether using floor here is safe.
    output_true_image_shapes = tf.ceil(
        tf.cast(true_image_shapes, tf.float32) / self._stride)
    valid_anchor_weights = get_valid_anchor_weights_in_flattened_image(
        output_true_image_shapes, output_height, output_width)
    valid_anchor_weights = tf.expand_dims(valid_anchor_weights, 2)

    object_center_loss = self._compute_object_center_loss(
        object_center_predictions=prediction_dict[OBJECT_CENTER],
        input_height=input_height,
        input_width=input_width,
        per_pixel_weights=valid_anchor_weights,
        maximum_normalized_coordinate=maximum_normalized_coordinate)
    losses = {
        OBJECT_CENTER:
            self._center_params.object_center_loss_weight * object_center_loss
    }
    if self._od_params is not None:
      od_losses = self._compute_object_detection_losses(
          input_height=input_height,
          input_width=input_width,
          prediction_dict=prediction_dict,
          per_pixel_weights=valid_anchor_weights,
          maximum_normalized_coordinate=maximum_normalized_coordinate)
      for key in od_losses:
        od_losses[key] = od_losses[key] * self._od_params.task_loss_weight
      losses.update(od_losses)

    if self._kp_params_dict is not None:
      for task_name, params in self._kp_params_dict.items():
        kp_losses = self._compute_keypoint_estimation_losses(
            task_name=task_name,
            input_height=input_height,
            input_width=input_width,
            prediction_dict=prediction_dict,
            per_pixel_weights=valid_anchor_weights)
        for key in kp_losses:
          kp_losses[key] = kp_losses[key] * params.task_loss_weight
        losses.update(kp_losses)

    if self._mask_params is not None:
      seg_losses = self._compute_segmentation_losses(
          prediction_dict=prediction_dict,
          per_pixel_weights=valid_anchor_weights)
      for key in seg_losses:
        seg_losses[key] = seg_losses[key] * self._mask_params.task_loss_weight
      losses.update(seg_losses)

    if self._densepose_params is not None:
      densepose_losses = self._compute_densepose_losses(
          input_height=input_height,
          input_width=input_width,
          prediction_dict=prediction_dict)
      for key in densepose_losses:
        densepose_losses[key] = (
            densepose_losses[key] * self._densepose_params.task_loss_weight)
      losses.update(densepose_losses)

    if self._track_params is not None:
      track_losses = self._compute_track_losses(
          input_height=input_height,
          input_width=input_width,
          prediction_dict=prediction_dict)
      for key in track_losses:
        track_losses[key] = (
            track_losses[key] * self._track_params.task_loss_weight)
      losses.update(track_losses)

    if self._temporal_offset_params is not None:
      offset_losses = self._compute_temporal_offset_loss(
          input_height=input_height,
          input_width=input_width,
          prediction_dict=prediction_dict)
      for key in offset_losses:
        offset_losses[key] = (
            offset_losses[key] * self._temporal_offset_params.task_loss_weight)
      losses.update(offset_losses)

    # Prepend the LOSS_KEY_PREFIX to the keys in the dictionary such that the
    # losses will be grouped together in Tensorboard.
    return dict([('%s/%s' % (LOSS_KEY_PREFIX, key), val)
                 for key, val in losses.items()])