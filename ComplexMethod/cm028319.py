def predict(self, preprocessed_inputs, true_image_shapes):
    """Predicts unpostprocessed tensors from input tensor.

    This function takes an input batch of images and runs it through the forward
    pass of the network to yield unpostprocessesed predictions.

    A side effect of calling the predict method is that self._anchors is
    populated with a box_list.BoxList of anchors.  These anchors must be
    constructed before the postprocess or loss functions can be called.

    Args:
      preprocessed_inputs: a [batch, height, width, channels] image tensor.
      true_image_shapes: int32 tensor of shape [batch, 3] where each row is
        of the form [height, width, channels] indicating the shapes
        of true images in the resized images, as resized images can be padded
        with zeros.

    Returns:
      prediction_dict: a dictionary holding "raw" prediction tensors:
        1) preprocessed_inputs: the [batch, height, width, channels] image
          tensor.
        2) box_encodings: 4-D float tensor of shape [batch_size, num_anchors,
          box_code_dimension] containing predicted boxes.
        3) class_predictions_with_background: 3-D float tensor of shape
          [batch_size, num_anchors, num_classes+1] containing class predictions
          (logits) for each of the anchors.  Note that this tensor *includes*
          background class predictions (at class index 0).
        4) feature_maps: a list of tensors where the ith tensor has shape
          [batch, height_i, width_i, depth_i].
        5) anchors: 2-D float tensor of shape [num_anchors, 4] containing
          the generated anchors in normalized coordinates.
        6) final_anchors: 3-D float tensor of shape [batch_size, num_anchors, 4]
          containing the generated anchors in normalized coordinates.
        If self._return_raw_detections_during_predict is True, the dictionary
        will also contain:
        7) raw_detection_boxes: a 4-D float32 tensor with shape
          [batch_size, self.max_num_proposals, 4] in normalized coordinates.
        8) raw_detection_feature_map_indices: a 3-D int32 tensor with shape
          [batch_size, self.max_num_proposals].
    """
    if self._inplace_batchnorm_update:
      batchnorm_updates_collections = None
    else:
      batchnorm_updates_collections = tf.GraphKeys.UPDATE_OPS
    if self._feature_extractor.is_keras_model:
      feature_maps = self._feature_extractor(preprocessed_inputs)
    else:
      with slim.arg_scope([slim.batch_norm],
                          is_training=(self._is_training and
                                       not self._freeze_batchnorm),
                          updates_collections=batchnorm_updates_collections):
        with tf.variable_scope(None, self._extract_features_scope,
                               [preprocessed_inputs]):
          feature_maps = self._feature_extractor.extract_features(
              preprocessed_inputs)

    feature_map_spatial_dims = self._get_feature_map_spatial_dims(
        feature_maps)
    logging.info('feature_map_spatial_dims: %s', feature_map_spatial_dims)
    image_shape = shape_utils.combined_static_and_dynamic_shape(
        preprocessed_inputs)
    boxlist_list = self._anchor_generator.generate(
        feature_map_spatial_dims,
        im_height=image_shape[1],
        im_width=image_shape[2])
    self._anchors = box_list_ops.concatenate(boxlist_list)
    if self._box_predictor.is_keras_model:
      predictor_results_dict = self._box_predictor(feature_maps)
    else:
      with slim.arg_scope([slim.batch_norm],
                          is_training=(self._is_training and
                                       not self._freeze_batchnorm),
                          updates_collections=batchnorm_updates_collections):
        predictor_results_dict = self._box_predictor.predict(
            feature_maps, self._anchor_generator.num_anchors_per_location())
    predictions_dict = {
        'preprocessed_inputs':
            preprocessed_inputs,
        'feature_maps':
            feature_maps,
        'anchors':
            self._anchors.get(),
        'final_anchors':
            tf.tile(
                tf.expand_dims(self._anchors.get(), 0), [image_shape[0], 1, 1])
    }
    for prediction_key, prediction_list in iter(predictor_results_dict.items()):
      prediction = tf.concat(prediction_list, axis=1)
      if (prediction_key == 'box_encodings' and prediction.shape.ndims == 4 and
          prediction.shape[2] == 1):
        prediction = tf.squeeze(prediction, axis=2)
      predictions_dict[prediction_key] = prediction
    if self._return_raw_detections_during_predict:
      predictions_dict.update(self._raw_detections_and_feature_map_inds(
          predictions_dict['box_encodings'], boxlist_list))
    self._batched_prediction_tensor_names = [x for x in predictions_dict
                                             if x != 'anchors']
    return predictions_dict