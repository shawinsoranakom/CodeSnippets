def _diff_capnp_values(v1, v2, path, tolerance):
  if isinstance(v1, _DynamicStructReader):
    yield from _diff_capnp(v1, v2, path, tolerance)

  elif isinstance(v1, _DynamicListReader):
    dot = '.'.join(path)
    n1, n2 = len(v1), len(v2)
    n = min(n1, n2)
    for i in range(n):
      yield from _diff_capnp_values(v1[i], v2[i], path + (str(i),), tolerance)
    if n2 > n:
      yield 'add', dot, [(i, v2[i]) for i in range(n, n2)]
    if n1 > n:
      yield 'remove', dot, list(reversed([(i, v1[i]) for i in range(n, n1)]))

  elif isinstance(v1, _DynamicEnum):
    s1, s2 = str(v1), str(v2)
    if s1 != s2:
      yield 'change', '.'.join(path), (s1, s2)

  elif isinstance(v1, float):
    if not (v1 == v2 or (
      math.isfinite(v1) and math.isfinite(v2) and
      abs(v1 - v2) <= max(tolerance, tolerance * max(abs(v1), abs(v2)))
    )):
      yield 'change', '.'.join(path), (v1, v2)

  else:
    if v1 != v2:
      yield 'change', '.'.join(path), (v1, v2)