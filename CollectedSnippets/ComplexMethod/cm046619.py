def load_progress(self) -> Optional[dict]:
        """Return live model-load progress, or None if not loading.

        While llama-server is warming up, its process is typically in
        kernel state D (disk sleep) mmap'ing the weight shards into
        page cache before pushing layers to VRAM. During that window
        ``/api/inference/status`` only reports ``loading``, which gives
        the UI nothing to display besides a spinner that looks stuck
        for minutes on large MoE models.

        This method samples ``/proc/<pid>/status VmRSS`` against the
        sum of the GGUF shard sizes so the UI can render a real bar
        and compute rate / ETA. Returns ``None`` when no load is in
        flight (no process, or process already healthy).

        Shape::

            {
                "phase": "mmap" | "ready",
                "bytes_loaded": int,   # VmRSS of the llama-server
                "bytes_total":  int,   # sum of shard file sizes
                "fraction": float,     # bytes_loaded / bytes_total, 0..1
            }

        Linux-only in the current implementation. On macOS/Windows the
        equivalent would be a different API; this returns ``None`` on
        platforms where ``/proc/<pid>/status`` is unavailable.
        """
        proc = self._process
        if proc is None:
            return None
        pid = proc.pid
        if pid is None:
            return None

        # Sum up shard sizes (primary + any extras sitting alongside).
        bytes_total = 0
        gguf_path = self._gguf_path
        if gguf_path:
            primary = Path(gguf_path)
            try:
                if primary.is_file():
                    bytes_total += primary.stat().st_size
            except OSError:
                pass
            # Extra shards live alongside the primary with the same prefix
            # before the shard index (e.g. ``-00001-of-00004.gguf``).
            try:
                parent = primary.parent
                stem = primary.name
                m = _SHARD_RE.match(stem)
                prefix = m.group(1) if m else None
                if prefix and parent.is_dir():
                    for sibling in parent.iterdir():
                        if (
                            sibling.is_file()
                            and sibling.name.startswith(prefix)
                            and sibling.name != stem
                            and sibling.suffix == ".gguf"
                        ):
                            try:
                                bytes_total += sibling.stat().st_size
                            except OSError:
                                pass
            except OSError:
                pass

        # Read VmRSS from /proc/<pid>/status. Kilobytes on Linux.
        bytes_loaded = 0
        try:
            with open(f"/proc/{pid}/status", "r", encoding = "utf-8") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        kb = int(line.split()[1])
                        bytes_loaded = kb * 1024
                        break
        except (FileNotFoundError, PermissionError, ValueError, OSError):
            return None

        phase = "ready" if self._healthy else "mmap"
        fraction = 0.0
        if bytes_total > 0:
            fraction = min(1.0, bytes_loaded / bytes_total)
        return {
            "phase": phase,
            "bytes_loaded": bytes_loaded,
            "bytes_total": bytes_total,
            "fraction": round(fraction, 4),
        }