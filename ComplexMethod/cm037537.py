def _maybe_evict(self, exclude: Path | None = None) -> None:
        """Evict expired entries first, then LRU until under size limit."""
        cache_dir = Path(self._media_cache_dir)  # type: ignore[arg-type]
        entries = []
        expired = []
        total_size = 0
        now = time.time()
        for f in cache_dir.iterdir():
            if f.name.startswith("."):
                continue
            try:
                stat = f.stat()
            except OSError:
                continue
            age = now - stat.st_mtime
            if age > self._media_cache_ttl_secs:
                expired.append(f)
                continue
            total_size += stat.st_size
            # Never evict the file we just wrote
            if exclude is not None and f.name == exclude.name:
                continue
            entries.append((stat.st_mtime, stat.st_size, f))

        # Evict items according to LRU policy
        entries.sort(key=lambda e: e[0], reverse=True)
        while total_size > self._media_cache_max_bytes and entries:
            mtime, size, f = entries.pop()
            expired.append(f)
            total_size -= size

        for f in expired:
            f.unlink(missing_ok=True)