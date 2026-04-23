def __next__(self) -> Any:
  if self._cur is None:
     raise StopIteration
  val = self._cur.val
  self._cur = self._cur.next_node
  return val
