def process_table_rows(by_proc, total_mb, use_pss, show_detail):
  """Build table rows. Returns (rows, total_row)."""
  mem_key = 'pss' if use_pss else 'rss'
  rows = []
  for name in sorted(by_proc, key=lambda n: np.mean(by_proc[n][mem_key]), reverse=True):
    m = by_proc[name]
    vals = m[mem_key]
    avg = round(np.mean(vals))
    row = [name, f"{avg} MB", f"{round(np.max(vals))} MB", f"{round(pct(avg, total_mb), 1)}%"]
    if show_detail:
      row.append(f"{round(np.mean(m['pss_anon']))} MB")
      row.append(f"{round(np.mean(m['pss_shmem']))} MB")
    rows.append(row)

  # Total row
  total_row = None
  if by_proc:
    max_samples = max(len(v[mem_key]) for v in by_proc.values())
    totals = []
    for i in range(max_samples):
      s = sum(v[mem_key][i] for v in by_proc.values() if i < len(v[mem_key]))
      totals.append(s)
    avg_total = round(np.mean(totals))
    total_row = ["TOTAL", f"{avg_total} MB", f"{round(np.max(totals))} MB", f"{round(pct(avg_total, total_mb), 1)}%"]
    if show_detail:
      total_row.append(f"{round(sum(np.mean(v['pss_anon']) for v in by_proc.values()))} MB")
      total_row.append(f"{round(sum(np.mean(v['pss_shmem']) for v in by_proc.values()))} MB")

  return rows, total_row