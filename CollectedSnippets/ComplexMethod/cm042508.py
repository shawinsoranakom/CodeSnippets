def auto_source(identifier: str, sources: list[Source], default_mode: ReadMode) -> list[str]:
  exceptions = {}

  sr = SegmentRange(identifier)
  needed_seg_idxs = sr.seg_idxs

  mode = default_mode if sr.selector is None else ReadMode(sr.selector)
  if mode == ReadMode.QLOG:
    try_fns = [FileName.QLOG]
  else:
    try_fns = [FileName.RLOG]

  # If selector allows it, fallback to qlogs
  if mode in (ReadMode.AUTO, ReadMode.AUTO_INTERACTIVE):
    try_fns.append(FileName.QLOG)

  # Build a dict of valid files as we evaluate each source. May contain mix of rlogs, qlogs, and None.
  # This function only returns when we've sourced all files, or throws an exception
  valid_files: dict[int, str] = {}
  for fn in try_fns:
    for source in sources:
      try:
        files = source(sr, needed_seg_idxs, fn)

        # Build a dict of valid files
        valid_files |= files

        # Don't check for segment files that have already been found
        needed_seg_idxs = [idx for idx in needed_seg_idxs if idx not in valid_files]

        # We've found all files, return them
        if len(needed_seg_idxs) == 0:
          return list(valid_files.values())
        else:
          raise FileNotFoundError(f"Did not find {fn} for seg idxs {needed_seg_idxs} of {sr.route_name}")

      except Exception as e:
        exceptions[source.__name__] = e

    if fn == try_fns[0]:
      missing_logs = len(needed_seg_idxs)
      if mode == ReadMode.AUTO:
        cloudlog.warning(f"{missing_logs}/{len(sr.seg_idxs)} rlogs were not found, falling back to qlogs for those segments...")
      elif mode == ReadMode.AUTO_INTERACTIVE:
        if input(f"{missing_logs}/{len(sr.seg_idxs)} rlogs were not found, would you like to fallback to qlogs for those segments? (y/N) ").lower() != "y":
          break

  missing_logs = len(needed_seg_idxs)
  raise LogsUnavailable(f"{missing_logs}/{len(sr.seg_idxs)} logs were not found, please ensure all logs " +
                        "are uploaded. You can fall back to qlogs with '/a' selector at the end of the route name.\n\n" +
                        "Exceptions for sources:\n  - " + "\n  - ".join([f"{k}: {repr(v)}" for k, v in exceptions.items()]))