def _convert_index(index, pos, m=None, is_start=True):
  """Converts index."""
  if index[pos] is not None:
    return index[pos]
  n = len(index)
  rear = pos
  while rear < n - 1 and index[rear] is None:
    rear += 1
  front = pos
  while front > 0 and index[front] is None:
    front -= 1
  assert index[front] is not None or index[rear] is not None
  if index[front] is None:
    if index[rear] >= 1:  # pytype: disable=unsupported-operands
      if is_start:
        return 0
      else:
        return index[rear] - 1
    return index[rear]
  if index[rear] is None:
    if m is not None and index[front] < m - 1:
      if is_start:
        return index[front] + 1
      else:
        return m - 1
    return index[front]
  if is_start:
    if index[rear] > index[front] + 1:
      return index[front] + 1
    else:
      return index[rear]
  else:
    if index[rear] > index[front] + 1:
      return index[rear] - 1
    else:
      return index[front]