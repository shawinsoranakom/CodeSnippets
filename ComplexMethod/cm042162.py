def print_report(proc_logs, device_states=None):
  """Print full memory analysis report. Can be called from tests or CLI."""
  if not proc_logs:
    print("No procLog messages found")
    return

  print(f"{len(proc_logs)} procLog samples, {len(device_states or [])} deviceState samples")

  use_pss = has_pss(proc_logs)
  if not use_pss:
    print("  (no PSS data — re-record with updated proclogd for accurate numbers)")

  total_mb = print_summary(proc_logs, device_states or [])

  by_proc = collect_per_process_mem(proc_logs, use_pss)
  op_procs = {n: v for n, v in by_proc.items() if is_openpilot_proc(n)}
  other_procs = {n: v for n, v in by_proc.items() if not is_openpilot_proc(n)}

  print_process_tables(op_procs, other_procs, total_mb, use_pss)
  print_memory_accounting(proc_logs, op_procs, other_procs, total_mb, use_pss)