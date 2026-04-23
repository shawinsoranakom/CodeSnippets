def ap_at_n(predictions, actuals, n=20, total_num_positives=None):
    """Calculate the non-interpolated average precision.

    Args:
      predictions: a numpy 1-D array storing the sparse prediction scores.
      actuals: a numpy 1-D array storing the ground truth labels. Any value
        larger than 0 will be treated as positives, otherwise as negatives.
      n: the top n items to be considered in ap@n.
      total_num_positives : (optionally) you can specify the number of total
        positive in the list. If specified, it will be used in calculation.

    Returns:
      The non-interpolated average precision at n.
      If n is larger than the length of the ranked list,
      the average precision will be returned.

    Raises:
      ValueError: An error occurred when
      1) the format of the input is not the numpy 1-D array;
      2) the shape of predictions and actuals does not match;
      3) the input n is not a positive integer.
    """
    if len(predictions) != len(actuals):
      raise ValueError("the shape of predictions and actuals does not match.")

    if n is not None:
      if not isinstance(n, int) or n <= 0:
        raise ValueError("n must be 'None' or a positive integer."
                         " It was '%s'." % n)

    ap = 0.0

    predictions = numpy.array(predictions)
    actuals = numpy.array(actuals)

    # add a shuffler to avoid overestimating the ap
    predictions, actuals = AveragePrecisionCalculator._shuffle(
        predictions, actuals)
    sortidx = sorted(
        range(len(predictions)), key=lambda k: predictions[k], reverse=True)

    if total_num_positives is None:
      numpos = numpy.size(numpy.where(actuals > 0))
    else:
      numpos = total_num_positives

    if numpos == 0:
      return 0

    if n is not None:
      numpos = min(numpos, n)
    delta_recall = 1.0 / numpos
    poscount = 0.0

    # calculate the ap
    r = len(sortidx)
    if n is not None:
      r = min(r, n)
    for i in range(r):
      if actuals[sortidx[i]] > 0:
        poscount += 1
        ap += poscount / (i + 1) * delta_recall
    return ap