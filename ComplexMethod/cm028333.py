def updates(self):
    """Returns a list of update operators for this model.

    Returns a list of update operators for this model that must be executed at
    each training step. The estimator's train op needs to have a control
    dependency on these updates.

    Returns:
      A list of update operators.
    """
    update_ops = []
    slim_update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
    # Copy the slim ops to avoid modifying the collection
    if slim_update_ops:
      update_ops.extend(slim_update_ops)
    # Passing None to get_updates_for grabs updates that should always be
    # executed and don't depend on any model inputs in the graph.
    # (E.g. if there was some count that should be incremented every time a
    # model is run).
    #
    # Passing inputs grabs updates that are transitively computed from the
    # model inputs being passed in.
    # (E.g. a batchnorm update depends on the observed inputs)
    if self._feature_extractor_for_proposal_features:
      if (self._feature_extractor_for_proposal_features !=
          _UNINITIALIZED_FEATURE_EXTRACTOR):
        update_ops.extend(
            self._feature_extractor_for_proposal_features.get_updates_for(None))
        update_ops.extend(
            self._feature_extractor_for_proposal_features.get_updates_for(
                self._feature_extractor_for_proposal_features.inputs))
    if isinstance(self._first_stage_box_predictor_first_conv,
                  tf.keras.Model):
      update_ops.extend(
          self._first_stage_box_predictor_first_conv.get_updates_for(
              None))
      update_ops.extend(
          self._first_stage_box_predictor_first_conv.get_updates_for(
              self._first_stage_box_predictor_first_conv.inputs))
    if self._first_stage_box_predictor.is_keras_model:
      update_ops.extend(
          self._first_stage_box_predictor.get_updates_for(None))
      update_ops.extend(
          self._first_stage_box_predictor.get_updates_for(
              self._first_stage_box_predictor.inputs))
    if self._feature_extractor_for_box_classifier_features:
      if (self._feature_extractor_for_box_classifier_features !=
          _UNINITIALIZED_FEATURE_EXTRACTOR):
        update_ops.extend(
            self._feature_extractor_for_box_classifier_features.get_updates_for(
                None))
        update_ops.extend(
            self._feature_extractor_for_box_classifier_features.get_updates_for(
                self._feature_extractor_for_box_classifier_features.inputs))
    if self._mask_rcnn_box_predictor:
      if self._mask_rcnn_box_predictor.is_keras_model:
        update_ops.extend(
            self._mask_rcnn_box_predictor.get_updates_for(None))
        update_ops.extend(
            self._mask_rcnn_box_predictor.get_updates_for(
                self._mask_rcnn_box_predictor.inputs))
    return update_ops