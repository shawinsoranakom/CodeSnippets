def _read_smaps(pid: int) -> SmapsData:
  global _smaps_path
  try:
    if _smaps_path is None:
      _smaps_path = 'smaps_rollup' if os.path.exists(f'/proc/{pid}/smaps_rollup') else 'smaps'

    result: SmapsData = {'pss': 0, 'pss_anon': 0, 'pss_shmem': 0}
    with open(f'/proc/{pid}/{_smaps_path}', 'rb') as f:
      for line in f:
        parts = line.split()
        if len(parts) >= 2 and parts[0] in _SMAPS_KEYS:
          val = int(parts[1]) * 1024  # kB -> bytes
          if parts[0] == b'Pss:':
            result['pss'] += val
          elif parts[0] == b'Pss_Anon:':
            result['pss_anon'] += val
          elif parts[0] == b'Pss_Shmem:':
            result['pss_shmem'] += val
    return result
  except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
    return {'pss': 0, 'pss_anon': 0, 'pss_shmem': 0}