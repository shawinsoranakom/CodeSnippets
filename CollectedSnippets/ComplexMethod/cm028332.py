def regularization_losses(self):
    """Returns a list of regularization losses for this model.

    Returns a list of regularization losses for this model that the estimator
    needs to use during training/optimization.

    Returns:
      A list of regularization loss tensors.
    """
    all_losses = []
    slim_losses = tf.get_collection(tf.GraphKeys.REGULARIZATION_LOSSES)
    # Copy the slim losses to avoid modifying the collection
    if slim_losses:
      all_losses.extend(slim_losses)
    # TODO(kaftan): Possibly raise an error if the feature extractors are
    # uninitialized in Keras.
    if self._feature_extractor_for_proposal_features:
      if (self._feature_extractor_for_proposal_features !=
          _UNINITIALIZED_FEATURE_EXTRACTOR):
        all_losses.extend(self._feature_extractor_for_proposal_features.losses)
    if isinstance(self._first_stage_box_predictor_first_conv,
                  tf.keras.Model):
      all_losses.extend(
          self._first_stage_box_predictor_first_conv.losses)
    if self._first_stage_box_predictor.is_keras_model:
      all_losses.extend(self._first_stage_box_predictor.losses)
    if self._feature_extractor_for_box_classifier_features:
      if (self._feature_extractor_for_box_classifier_features !=
          _UNINITIALIZED_FEATURE_EXTRACTOR):
        all_losses.extend(
            self._feature_extractor_for_box_classifier_features.losses)
    if self._mask_rcnn_box_predictor:
      if self._mask_rcnn_box_predictor.is_keras_model:
        all_losses.extend(self._mask_rcnn_box_predictor.losses)
    return all_losses