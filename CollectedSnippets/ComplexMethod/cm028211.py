def _predict(self, image_features, num_predictions_per_location_list):
    """Computes encoded object locations and corresponding confidences.

    Args:
      image_features: A list of float tensors of shape [batch_size, height_i,
        width_i, channels] containing features for a batch of images. Note that
        when not all tensors in the list have the same number of channels, an
        additional projection layer will be added on top the tensor to generate
        feature map with number of channels consitent with the majority.
      num_predictions_per_location_list: A list of integers representing the
        number of box predictions to be made per spatial location for each
        feature map. Note that all values must be the same since the weights are
        shared.

    Returns:
      A dictionary containing:
        box_encodings: A list of float tensors of shape
          [batch_size, num_anchors_i, code_size] representing the location of
          the objects. Each entry in the list corresponds to a feature map in
          the input `image_features` list.
        class_predictions_with_background: A list of float tensors of shape
          [batch_size, num_anchors_i, num_classes + 1] representing the class
          predictions for the proposals. Each entry in the list corresponds to a
          feature map in the input `image_features` list.
        (optional) Predictions from other heads.
          E.g., mask_predictions: A list of float tensors of shape
          [batch_size, num_anchord_i, num_classes, mask_height, mask_width].


    Raises:
      ValueError: If the num predictions per locations differs between the
        feature maps.
    """
    if len(set(num_predictions_per_location_list)) > 1:
      raise ValueError('num predictions per location must be same for all'
                       'feature maps, found: {}'.format(
                           num_predictions_per_location_list))
    feature_channels = [
        shape_utils.get_dim_as_int(image_feature.shape[3])
        for image_feature in image_features
    ]
    has_different_feature_channels = len(set(feature_channels)) > 1
    if has_different_feature_channels:
      inserted_layer_counter = 0
      target_channel = max(set(feature_channels), key=feature_channels.count)
      tf.logging.info('Not all feature maps have the same number of '
                      'channels, found: {}, appending additional projection '
                      'layers to bring all feature maps to uniformly have {} '
                      'channels.'.format(feature_channels, target_channel))
    else:
      # Place holder variables if has_different_feature_channels is False.
      target_channel = -1
      inserted_layer_counter = -1
    predictions = {
        BOX_ENCODINGS: [],
        CLASS_PREDICTIONS_WITH_BACKGROUND: [],
    }
    for head_name in self._other_heads.keys():
      predictions[head_name] = []
    for feature_index, (image_feature,
                        num_predictions_per_location) in enumerate(
                            zip(image_features,
                                num_predictions_per_location_list)):
      with tf.variable_scope('WeightSharedConvolutionalBoxPredictor',
                             reuse=tf.AUTO_REUSE):
        with slim.arg_scope(self._conv_hyperparams_fn()):
          # TODO(wangjiang) Pass is_training to the head class directly.
          with slim.arg_scope([slim.dropout], is_training=self._is_training):
            (image_feature,
             inserted_layer_counter) = self._insert_additional_projection_layer(
                 image_feature, inserted_layer_counter, target_channel)
            if self._share_prediction_tower:
              box_tower_scope = 'PredictionTower'
            else:
              box_tower_scope = 'BoxPredictionTower'
            box_tower_feature = self._compute_base_tower(
                tower_name_scope=box_tower_scope,
                image_feature=image_feature,
                feature_index=feature_index)
            box_encodings = self._box_prediction_head.predict(
                features=box_tower_feature,
                num_predictions_per_location=num_predictions_per_location)
            predictions[BOX_ENCODINGS].append(box_encodings)
            sorted_keys = sorted(self._other_heads.keys())
            sorted_keys.append(CLASS_PREDICTIONS_WITH_BACKGROUND)
            for head_name in sorted_keys:
              if head_name == CLASS_PREDICTIONS_WITH_BACKGROUND:
                head_obj = self._class_prediction_head
              else:
                head_obj = self._other_heads[head_name]
              prediction = self._predict_head(
                  head_name=head_name,
                  head_obj=head_obj,
                  image_feature=image_feature,
                  box_tower_feature=box_tower_feature,
                  feature_index=feature_index,
                  num_predictions_per_location=num_predictions_per_location)
              predictions[head_name].append(prediction)
    return predictions