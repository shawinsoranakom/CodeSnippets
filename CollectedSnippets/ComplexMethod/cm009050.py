def __post_init__(self) -> None:
        super().__post_init__()
        if self.memory_bytes is not None and self.memory_bytes <= 0:
            msg = "memory_bytes must be positive if provided."
            raise ValueError(msg)
        if self.cpu_time_seconds is not None:
            msg = (
                "DockerExecutionPolicy does not support cpu_time_seconds; configure CPU limits "
                "using Docker run options such as '--cpus'."
            )
            raise RuntimeError(msg)
        if self.cpus is not None and not self.cpus.strip():
            msg = "cpus must be a non-empty string when provided."
            raise ValueError(msg)
        if self.user is not None and not self.user.strip():
            msg = "user must be a non-empty string when provided."
            raise ValueError(msg)
        self.extra_run_args = tuple(self.extra_run_args or ())