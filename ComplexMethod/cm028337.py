def compute_precision_recall(scores, labels, num_gt):
  """Compute precision and recall.

  Args:
    scores: A float numpy array representing detection score
    labels: A float numpy array representing weighted true/false positive labels
    num_gt: Number of ground truth instances

  Raises:
    ValueError: if the input is not of the correct format

  Returns:
    precision: Fraction of positive instances over detected ones. This value is
      None if no ground truth labels are present.
    recall: Fraction of detected positive instance over all positive instances.
      This value is None if no ground truth labels are present.

  """
  if not isinstance(labels, np.ndarray) or len(labels.shape) != 1:
    raise ValueError("labels must be single dimension numpy array")

  if labels.dtype != float and labels.dtype != bool:
    raise ValueError("labels type must be either bool or float")

  if not isinstance(scores, np.ndarray) or len(scores.shape) != 1:
    raise ValueError("scores must be single dimension numpy array")

  if num_gt < np.sum(labels):
    raise ValueError("Number of true positives must be smaller than num_gt.")

  if len(scores) != len(labels):
    raise ValueError("scores and labels must be of the same size.")

  if num_gt == 0:
    return None, None

  sorted_indices = np.argsort(scores)
  sorted_indices = sorted_indices[::-1]
  true_positive_labels = labels[sorted_indices]
  false_positive_labels = (true_positive_labels <= 0).astype(float)
  cum_true_positives = np.cumsum(true_positive_labels)
  cum_false_positives = np.cumsum(false_positive_labels)
  precision = cum_true_positives.astype(float) / (
      cum_true_positives + cum_false_positives)
  recall = cum_true_positives.astype(float) / num_gt
  return precision, recall