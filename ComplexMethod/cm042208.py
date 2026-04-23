def diff_process(cfg, ref_msgs, new_msgs) -> tuple | None:
  ref = defaultdict(list)
  new = defaultdict(list)
  for m in ref_msgs:
    if m.which() in cfg.subs:
      ref[m.which()].append(m)
  for m in new_msgs:
    if m.which() in cfg.subs:
      new[m.which()].append(m)

  diffs = []
  for sub in cfg.subs:
    if len(ref[sub]) != len(new[sub]):
      diffs.append((f"{sub} (message count)", 0, (len(ref[sub]), len(new[sub])), 0))
    for i, (r, n) in enumerate(zip(ref[sub], new[sub], strict=False)):
      for d in compare_logs([r], [n], cfg.ignore, tolerance=cfg.tolerance):
        if d[0] == "change":
          a, b = d[2]
          if a != a and b != b:
            continue
          diffs.append((d[1], i, d[2], r.logMonoTime))
        elif d[0] in ("add", "remove"):
          for item in d[2]:
            if item[1] != item[1]:
              continue
            diffs.append((f"{d[1]}.{item[0]}", i, (d[0], item[1]), r.logMonoTime))
  return (diffs, ref, new) if diffs else None