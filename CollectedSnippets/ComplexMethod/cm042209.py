def diff_report(replay_diffs, segments) -> None:
  seg_to_plat = {seg: plat for plat, seg in segments}

  with_diffs, errors, n_passed = [], [], 0
  for seg, proc, data in replay_diffs:
    plat = seg_to_plat.get(seg, "UNKNOWN")
    if data is None:
      n_passed += 1
    elif isinstance(data, str):
      errors.append((plat, seg, proc, data))
    else:
      with_diffs.append((plat, seg, proc, data))

  icon = "⚠️" if with_diffs else "✅"
  lines = [
    "## Process replay diff report",
    "Replays driving segments through this PR and compares the behavior to master.",
    "Please review any changes carefully to ensure they are expected.\n",
    f"{icon}  {len(with_diffs)} changed, {n_passed} passed, {len(errors)} errors",
  ]

  for plat, seg, proc, err in errors:
    lines.append(f"\nERROR {plat} - {seg} [{proc}]: {err}")

  if with_diffs:
    lines.append("<details><summary><b>Show changes</b></summary>\n\n```")
    for plat, seg, proc, (diffs, ref, new) in with_diffs:
      lines.append(f"\n{plat} - {seg} [{proc}]")
      by_field = defaultdict(list)
      for d in diffs:
        by_field[d[0]].append(d)
      for field, fd in sorted(by_field.items()):
        lines.append(f"\n  {field} ({len(fd)} diffs)")
        lines.extend(diff_format(fd, ref, new, field))
    lines.append("```\n</details>")

  with open(os.path.join(PROC_REPLAY_DIR, "diff_report.txt"), "w") as f:
    f.write("\n".join(lines))