def __post_init__(self) -> None:
        super().__post_init__()
        if self.cpu_time_seconds is not None and self.cpu_time_seconds <= 0:
            msg = "cpu_time_seconds must be positive if provided."
            raise ValueError(msg)
        if self.memory_bytes is not None and self.memory_bytes <= 0:
            msg = "memory_bytes must be positive if provided."
            raise ValueError(msg)
        self._limits_requested = any(
            value is not None for value in (self.cpu_time_seconds, self.memory_bytes)
        )
        if self._limits_requested and not _HAS_RESOURCE:
            msg = (
                "HostExecutionPolicy cpu/memory limits require the Python 'resource' module. "
                "Either remove the limits or run on a POSIX platform."
            )
            raise RuntimeError(msg)