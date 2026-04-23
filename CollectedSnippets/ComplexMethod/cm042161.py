def print_memory_accounting(proc_logs, op_procs, other_procs, total_mb, use_pss):
  last = proc_logs[-1].procLog.mem
  used = (last.total - last.available) / MB
  shared = last.shared / MB
  cached_buf = (last.buffers + last.cached) / MB - shared  # shared (MSGQ) is in Cached; separate it
  msgq = shared

  mem_key = 'pss' if use_pss else 'rss'
  op_total = sum(v[mem_key][-1] for v in op_procs.values()) if op_procs else 0
  other_total = sum(v[mem_key][-1] for v in other_procs.values()) if other_procs else 0
  proc_sum = op_total + other_total
  remainder = used - (cached_buf + msgq) - proc_sum

  if not use_pss:
    # RSS double-counts shared; add back once to partially correct
    remainder += shared

  header = ["", "MB", "%", ""]
  label = "PSS" if use_pss else "RSS*"
  rows = [
    ["Used (total - avail)", f"{used:.0f}", f"{pct(used, total_mb):.1f}", "memory in use by the system"],
    ["  Cached + Buffers", f"{cached_buf:.0f}", f"{pct(cached_buf, total_mb):.1f}", "pagecache + fs metadata, reclaimable"],
    ["  MSGQ (shared)", f"{msgq:.0f}", f"{pct(msgq, total_mb):.1f}", "/dev/shm tmpfs, also in process PSS"],
    [f"  openpilot {label}", f"{op_total:.0f}", f"{pct(op_total, total_mb):.1f}", "sum of openpilot process memory"],
    [f"  other {label}", f"{other_total:.0f}", f"{pct(other_total, total_mb):.1f}", "sum of non-openpilot process memory"],
    ["  kernel/ION/GPU", f"{remainder:.0f}", f"{pct(remainder, total_mb):.1f}", "slab, ION/DMA-BUF, GPU, page tables"],
  ]
  note = "" if use_pss else " (*RSS overcounts shared mem)"
  print(f"\n-- Memory Accounting (last sample){note} --")
  print(tabulate(rows, header, tablefmt="simple_grid", stralign="right"))