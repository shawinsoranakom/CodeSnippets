def prune_cache(new_entry: str | None = None) -> None:
  """Evicts oldest cache files (LRU) until cache is under the size limit."""
  # we use a manifest to avoid tons of os.stat syscalls (slow)
  manifest = {}
  manifest_path = Paths.download_cache_root() + "manifest.txt"
  if os.path.exists(manifest_path):
    with open(manifest_path) as f:
      manifest = {parts[0]: int(parts[1]) for line in f if (parts := line.strip().split()) and len(parts) == 2}

  if new_entry:
    manifest[new_entry] = int(time.time())  # noqa: TID251

  # evict the least recently used files until under limit
  sorted_items = sorted(manifest.items(), key=lambda x: x[1])
  while len(manifest) * CHUNK_SIZE > CACHE_SIZE and sorted_items:
    key, _ = sorted_items.pop(0)
    try:
      os.remove(Paths.download_cache_root() + key)
    except OSError:
      pass
    manifest.pop(key, None)

  # write out manifest
  with atomic_write(manifest_path, mode="w", overwrite=True) as f:
    f.write('\n'.join(f"{k} {v}" for k, v in manifest.items()))