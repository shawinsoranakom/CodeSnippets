def _apply_post_spawn_limits(self, process: subprocess.Popen[str]) -> None:
        if not self._limits_requested or not self._can_use_prlimit():
            return
        if not _HAS_RESOURCE:  # pragma: no cover - defensive
            return
        pid = process.pid
        try:
            prlimit = typing.cast("typing.Any", resource).prlimit
            if self.cpu_time_seconds is not None:
                prlimit(pid, resource.RLIMIT_CPU, (self.cpu_time_seconds, self.cpu_time_seconds))
            if self.memory_bytes is not None:
                limit = (self.memory_bytes, self.memory_bytes)
                if hasattr(resource, "RLIMIT_AS"):
                    prlimit(pid, resource.RLIMIT_AS, limit)
                elif hasattr(resource, "RLIMIT_DATA"):
                    prlimit(pid, resource.RLIMIT_DATA, limit)
        except OSError as exc:  # pragma: no cover - depends on platform support
            msg = "Failed to apply resource limits via prlimit."
            raise RuntimeError(msg) from exc