def print_process_tables(op_procs, other_procs, total_mb, use_pss):
  all_procs = {**op_procs, **other_procs}
  show_detail = use_pss and _has_pss_detail(all_procs)

  header = ["process", "avg", "max", "%"]
  if show_detail:
    header += ["anon", "shmem"]

  op_rows, op_total = process_table_rows(op_procs, total_mb, use_pss, show_detail)
  # filter other: >5MB avg and not bare interpreter paths (test infra noise)
  other_filtered = {n: v for n, v in other_procs.items()
                    if np.mean(v['pss' if use_pss else 'rss']) > 5.0
                    and os.path.basename(n.split()[0]) not in ('python', 'python3')}
  other_rows, other_total = process_table_rows(other_filtered, total_mb, use_pss, show_detail)

  rows = op_rows
  if op_total:
    rows.append(op_total)
  if other_rows:
    sep_width = len(header)
    rows.append([""] * sep_width)
    rows.extend(other_rows)
    if other_total:
      other_total[0] = "TOTAL (other)"
      rows.append(other_total)

  metric = "PSS (no shared double-count)" if use_pss else "RSS (includes shared, overcounts)"
  print(f"\n-- Per-Process Memory: {metric} --")
  print(tabulate(rows, header, **TABULATE_OPTS))