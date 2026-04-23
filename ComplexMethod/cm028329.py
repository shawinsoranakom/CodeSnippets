def postprocess(self, prediction_dict, true_image_shapes):
    """Convert prediction tensors to final detections.

    This function converts raw predictions tensors to final detection results.
    See base class for output format conventions.  Note also that by default,
    scores are to be interpreted as logits, but if a score_converter is used,
    then scores are remapped (and may thus have a different interpretation).

    If number_of_stages=1, the returned results represent proposals from the
    first stage RPN and are padded to have self.max_num_proposals for each
    image; otherwise, the results can be interpreted as multiclass detections
    from the full two-stage model and are padded to self._max_detections.

    Args:
      prediction_dict: a dictionary holding prediction tensors (see the
        documentation for the predict method.  If number_of_stages=1, we
        expect prediction_dict to contain `rpn_box_encodings`,
        `rpn_objectness_predictions_with_background`, `rpn_features_to_crop`,
        and `anchors` fields.  Otherwise we expect prediction_dict to
        additionally contain `refined_box_encodings`,
        `class_predictions_with_background`, `num_proposals`,
        `proposal_boxes` and, optionally, `mask_predictions` fields.
      true_image_shapes: int32 tensor of shape [batch, 3] where each row is
        of the form [height, width, channels] indicating the shapes
        of true images in the resized images, as resized images can be padded
        with zeros.

    Returns:
      detections: a dictionary containing the following fields
        detection_boxes: [batch, max_detection, 4]
        detection_scores: [batch, max_detections]
        detection_multiclass_scores: [batch, max_detections, 2]
        detection_anchor_indices: [batch, max_detections]
        detection_classes: [batch, max_detections]
          (this entry is only created if rpn_mode=False)
        num_detections: [batch]
        raw_detection_boxes: [batch, total_detections, 4]
        raw_detection_scores: [batch, total_detections, num_classes + 1]

    Raises:
      ValueError: If `predict` is called before `preprocess`.
      ValueError: If `_output_final_box_features` is true but
        rpn_features_to_crop is not in the prediction_dict.
    """

    with tf.name_scope('FirstStagePostprocessor'):
      if self._number_of_stages == 1:

        image_shapes = self._image_batch_shape_2d(
            prediction_dict['image_shape'])
        (proposal_boxes, proposal_scores, proposal_multiclass_scores,
         num_proposals, raw_proposal_boxes,
         raw_proposal_scores) = self._postprocess_rpn(
             prediction_dict['rpn_box_encodings'],
             prediction_dict['rpn_objectness_predictions_with_background'],
             prediction_dict['anchors'], image_shapes, true_image_shapes)
        return {
            fields.DetectionResultFields.detection_boxes:
                proposal_boxes,
            fields.DetectionResultFields.detection_scores:
                proposal_scores,
            fields.DetectionResultFields.detection_multiclass_scores:
                proposal_multiclass_scores,
            fields.DetectionResultFields.num_detections:
                tf.cast(num_proposals, dtype=tf.float32),
            fields.DetectionResultFields.raw_detection_boxes:
                raw_proposal_boxes,
            fields.DetectionResultFields.raw_detection_scores:
                raw_proposal_scores
        }

    # TODO(jrru): Remove mask_predictions from _post_process_box_classifier.
    if (self._number_of_stages == 2 or
        (self._number_of_stages == 3 and self._is_training)):
      with tf.name_scope('SecondStagePostprocessor'):
        mask_predictions = prediction_dict.get(box_predictor.MASK_PREDICTIONS)
        detections_dict = self._postprocess_box_classifier(
            prediction_dict['refined_box_encodings'],
            prediction_dict['class_predictions_with_background'],
            prediction_dict['proposal_boxes'],
            prediction_dict['num_proposals'],
            true_image_shapes,
            mask_predictions=mask_predictions)

      if self._output_final_box_features:
        if 'rpn_features_to_crop' not in prediction_dict:
          raise ValueError(
              'Please make sure rpn_features_to_crop is in the prediction_dict.'
          )
        detections_dict[
            'detection_features'] = (
                self._add_detection_box_boxclassifier_features_output_node(
                    detections_dict[
                        fields.DetectionResultFields.detection_boxes],
                    prediction_dict['rpn_features_to_crop'],
                    prediction_dict['image_shape']))
      if self._output_final_box_rpn_features:
        if 'rpn_features_to_crop' not in prediction_dict:
          raise ValueError(
              'Please make sure rpn_features_to_crop is in the prediction_dict.'
          )
        detections_dict['cropped_rpn_box_features'] = (
            self._add_detection_box_rpn_features_output_node(
                detections_dict[fields.DetectionResultFields.detection_boxes],
                prediction_dict['rpn_features_to_crop'],
                prediction_dict['image_shape']))

      return detections_dict

    if self._number_of_stages == 3:
      # Post processing is already performed in 3rd stage. We need to transfer
      # postprocessed tensors from `prediction_dict` to `detections_dict`.
      # Remove any items from the prediction dictionary if they are not pure
      # Tensors.
      non_tensor_predictions = [
          k for k, v in prediction_dict.items() if not isinstance(v, tf.Tensor)]
      for k in non_tensor_predictions:
        tf.logging.info('Removing {0} from prediction_dict'.format(k))
        prediction_dict.pop(k)
      return prediction_dict