def compare_logs(log1, log2, ignore_fields=None, ignore_msgs=None, tolerance=None,):
  if ignore_fields is None:
    ignore_fields = []
  if ignore_msgs is None:
    ignore_msgs = []
  tolerance = EPSILON if tolerance is None else tolerance

  log1, log2 = (
    [m for m in log if m.which() not in ignore_msgs]
    for log in (log1, log2)
  )

  if len(log1) != len(log2):
    cnt1 = Counter(m.which() for m in log1)
    cnt2 = Counter(m.which() for m in log2)
    raise Exception(f"logs are not same length: {len(log1)} VS {len(log2)}\n\t\t{cnt1}\n\t\t{cnt2}")

  diff = []
  for msg1, msg2 in zip(log1, log2, strict=True):
    if msg1.which() != msg2.which():
      raise Exception("msgs not aligned between logs")

    msg1 = remove_ignored_fields(msg1, ignore_fields)
    msg2 = remove_ignored_fields(msg2, ignore_fields)

    if msg1.to_bytes() != msg2.to_bytes():
      dd = list(_diff_capnp(msg1.as_reader(), msg2.as_reader(), (), tolerance))
      diff.extend(dd)
  return diff