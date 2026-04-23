def update_state(self, groundtruths, predictions):
    """Update and aggregate detection results and ground-truth data.

    Args:
      groundtruths: a dictionary of Tensors including the fields below.
        See also different parsers under `../dataloader` for more details.
        Required fields:
          - source_id: a numpy array of int or string of shape [batch_size].
          - height: a numpy array of int of shape [batch_size].
          - width: a numpy array of int of shape [batch_size].
          - num_detections: a numpy array of int of shape [batch_size].
          - boxes: a numpy array of float of shape [batch_size, K, 4].
          - classes: a numpy array of int of shape [batch_size, K].
        Optional fields:
          - is_crowds: a numpy array of int of shape [batch_size, K]. If the
              field is absent, it is assumed that this instance is not crowd.
          - areas: a numy array of float of shape [batch_size, K]. If the
              field is absent, the area is calculated using either boxes or
              masks depending on which one is available.
          - masks: a numpy array of float of shape
              [batch_size, K, mask_height, mask_width],
      predictions: a dictionary of tensors including the fields below.
        See different parsers under `../dataloader` for more details.
        Required fields:
          - source_id: a numpy array of int or string of shape [batch_size].
          - image_info [if `need_rescale_bboxes` is True]: a numpy array of
            float of shape [batch_size, 4, 2].
          - num_detections: a numpy array of
            int of shape [batch_size].
          - detection_boxes: a numpy array of float of shape [batch_size, K, 4].
          - detection_classes: a numpy array of int of shape [batch_size, K].
          - detection_scores: a numpy array of float of shape [batch_size, K].
        Optional fields:
          - detection_masks: a numpy array of float of shape
              [batch_size, K, mask_height, mask_width].
    Raises:
      ValueError: if the required prediction or ground-truth fields are not
        present in the incoming `predictions` or `groundtruths`.
    """
    groundtruths, predictions = self._convert_to_numpy(groundtruths,
                                                       predictions)
    for k in self._required_prediction_fields:
      if k not in predictions:
        raise ValueError(
            'Missing the required key `{}` in predictions!'.format(k))
    if self._need_rescale_bboxes:
      self._process_bbox_predictions(predictions)
    if self._need_rescale_keypoints:
      self._process_keypoints_predictions(predictions)
    for k, v in six.iteritems(predictions):
      if k not in self._predictions:
        self._predictions[k] = [v]
      else:
        self._predictions[k].append(v)

    if not self._annotation_file:
      assert groundtruths
      for k in self._required_groundtruth_fields:
        if k not in groundtruths:
          raise ValueError(
              'Missing the required key `{}` in groundtruths!'.format(k))
      for k, v in six.iteritems(groundtruths):
        if k not in self._groundtruths:
          self._groundtruths[k] = [v]
        else:
          self._groundtruths[k].append(v)