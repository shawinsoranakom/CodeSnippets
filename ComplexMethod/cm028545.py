def accumulate(self, predictions, actuals, num_positives=None):
    """Accumulate the predictions and their ground truth labels.

    After the function call, we may call peek_ap_at_n to actually calculate
    the average precision.
    Note predictions and actuals must have the same shape.

    Args:
      predictions: a list storing the prediction scores.
      actuals: a list storing the ground truth labels. Any value larger than 0
        will be treated as positives, otherwise as negatives. num_positives = If
        the 'predictions' and 'actuals' inputs aren't complete, then it's
        possible some true positives were missed in them. In that case, you can
        provide 'num_positives' in order to accurately track recall.
      num_positives: number of positive examples.

    Raises:
      ValueError: An error occurred when the format of the input is not the
      numpy 1-D array or the shape of predictions and actuals does not match.
    """
    if len(predictions) != len(actuals):
      raise ValueError("the shape of predictions and actuals does not match.")

    if num_positives is not None:
      if not isinstance(num_positives, numbers.Number) or num_positives < 0:
        raise ValueError(
            "'num_positives' was provided but it was a negative number.")

    if num_positives is not None:
      self._total_positives += num_positives
    else:
      self._total_positives += numpy.size(
          numpy.where(numpy.array(actuals) > 1e-5))
    topk = self._top_n
    heap = self._heap

    for i in range(numpy.size(predictions)):
      if topk is None or len(heap) < topk:
        heapq.heappush(heap, (predictions[i], actuals[i]))
      else:
        if predictions[i] > heap[0][0]:  # heap[0] is the smallest
          heapq.heappop(heap)
          heapq.heappush(heap, (predictions[i], actuals[i]))