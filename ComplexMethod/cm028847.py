def update_state(self, groundtruths, predictions):
    """Update and aggregate detection results and ground-truth data.

    Args:
      groundtruths: a dictionary of Tensors including the fields below. See also
        different parsers under `../dataloader` for more details.
        Required fields:
          - category_mask: a numpy array of uint16 of shape [batch_size, H, W].
          - instance_mask: a numpy array of uint16 of shape [batch_size, H, W].
          - image_info: [batch, 4, 2], a tensor that holds information about
          original and preprocessed images. Each entry is in the format of
          [[original_height, original_width], [input_height, input_width],
          [y_scale, x_scale], [y_offset, x_offset]], where [desired_height,
          desired_width] is the actual scaled image size, and [y_scale, x_scale]
          is the scaling factor, which is the ratio of scaled dimension /
          original dimension.
      predictions: a dictionary of tensors including the fields below. See
        different parsers under `../dataloader` for more details.
        Required fields:
          - category_mask: a numpy array of uint16 of shape [batch_size, H, W].
          - instance_mask: a numpy array of uint16 of shape [batch_size, H, W].

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

    for k in self._required_groundtruth_fields:
      if k not in groundtruths:
        raise ValueError(
            'Missing the required key `{}` in groundtruths!'.format(k))

    if self._rescale_predictions:
      for idx in range(len(groundtruths['category_mask'])):
        image_info = groundtruths['image_info'][idx]
        groundtruths_ = {
            'category_mask':
                _crop_padding(groundtruths['category_mask'][idx], image_info),
            'instance_mask':
                _crop_padding(groundtruths['instance_mask'][idx], image_info),
            }
        predictions_ = {
            'category_mask':
                _crop_padding(predictions['category_mask'][idx], image_info),
            'instance_mask':
                _crop_padding(predictions['instance_mask'][idx], image_info),
            }
        groundtruths_, predictions_ = self._convert_to_numpy(
            groundtruths_, predictions_)

        self._pq_metric_module.compare_and_accumulate(
            groundtruths_, predictions_)
    else:
      for idx in range(len(groundtruths['category_mask'])):
        groundtruths_ = {
            'category_mask': groundtruths['category_mask'][idx],
            'instance_mask': groundtruths['instance_mask'][idx]
        }
        predictions_ = {
            'category_mask': predictions['category_mask'][idx],
            'instance_mask': predictions['instance_mask'][idx]
        }
        self._pq_metric_module.compare_and_accumulate(groundtruths_,
                                                      predictions_)