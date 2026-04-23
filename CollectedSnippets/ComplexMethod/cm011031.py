def __post_init__(self):
        default_timeout = 900
        if self.rdzv_timeout != -1:
            self.rdzv_configs["timeout"] = self.rdzv_timeout
        elif "timeout" not in self.rdzv_configs:
            self.rdzv_configs["timeout"] = default_timeout

        # Post-processing to enable refactoring to introduce logs_specs due to non-torchrun API usage
        if self.logs_specs is None:
            self.logs_specs = DefaultLogsSpecs()

        if (
            self.numa_options is None
            and torch.cuda.is_available()
            # We assume local_rank n uses cuda device n.
            and torch.cuda.device_count() == self.nproc_per_node
        ):
            self.numa_options = get_default_numa_options()
            logger.info("Using default numa options = %r", self.numa_options)

        # Set shutdown_timeout from environment variable if not explicitly set
        if self.shutdown_timeout is None:
            self.shutdown_timeout = int(
                os.environ.get("TORCH_ELASTIC_SHUTDOWN_TIMEOUT", "30")
            )
        elif self.shutdown_timeout < 0:
            raise ValueError(
                f"shutdown_timeout must be non-negative, got {self.shutdown_timeout}"
            )