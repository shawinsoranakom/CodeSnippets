def seg_idxs(self) -> list[int]:
    m = re.fullmatch(RE.SLICE, self.slice)
    assert m is not None, f"Invalid slice: {self.slice}"
    start, end, step = (None if s is None else int(s) for s in m.groups())

    # one segment specified
    if start is not None and end is None and ':' not in self.slice:
      if start < 0:
        start += get_max_seg_number_cached(self) + 1
      return [start]

    s = slice(start, end, step)
    # no specified end or using relative indexing, need number of segments
    if end is None or end < 0 or (start is not None and start < 0):
      return list(range(get_max_seg_number_cached(self) + 1))[s]
    else:
      return list(range(end + 1))[s]