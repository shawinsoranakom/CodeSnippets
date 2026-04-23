def _online_sample_mask(self, inputs: tf.Tensor,
                          boundary: tf.Tensor) -> tf.Tensor:
    """Samples target positions for predictions.

    Descriptions of each strategy:
      - 'single_token': Samples individual tokens as prediction targets.
      - 'token_span': Samples spans of tokens as prediction targets.
      - 'whole_word': Samples individual words as prediction targets.
      - 'word_span': Samples spans of words as prediction targets.

    Args:
      inputs: The input tokens.
      boundary: The `int` Tensor of indices indicating whole word boundaries.
        This is used in 'whole_word' and 'word_span'

    Returns:
      The sampled `bool` input mask.

    Raises:
      `ValueError`: if `max_predictions_per_seq` is not set or if boundary is
        not provided for 'whole_word' and 'word_span' sample strategies.
    """
    if self._max_predictions_per_seq is None:
      raise ValueError('`max_predictions_per_seq` must be set.')

    if boundary is None and 'word' in self._sample_strategy:
      raise ValueError('`boundary` must be provided for {} strategy'.format(
          self._sample_strategy))

    if self._sample_strategy == 'single_token':
      return self._single_token_mask(inputs)
    elif self._sample_strategy == 'token_span':
      return self._token_span_mask(inputs)
    elif self._sample_strategy == 'whole_word':
      return self._whole_word_mask(inputs, boundary)
    elif self._sample_strategy == 'word_span':
      return self._word_span_mask(inputs, boundary)
    else:
      raise NotImplementedError('Invalid sample strategy.')