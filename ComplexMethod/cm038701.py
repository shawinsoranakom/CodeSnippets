def _validate_profiler_config(self) -> Self:
        has_delay_or_limit = self.delay_iterations > 0 or self.max_iterations > 0
        if self.profiler == "torch" and has_delay_or_limit and not self.ignore_frontend:
            logger.warning_once(
                "Using 'torch' profiler with delay_iterations or max_iterations "
                "while ignore_frontend is False may result in high overhead."
            )

        profiler_dir = self.torch_profiler_dir
        if profiler_dir and self.profiler != "torch":
            raise ValueError(
                "torch_profiler_dir is only applicable when profiler is set to 'torch'"
            )
        if self.profiler == "torch" and not profiler_dir:
            raise ValueError("torch_profiler_dir must be set when profiler is 'torch'")

        # Support any URI scheme (gs://, s3://, hdfs://, etc.)
        # These paths should not be converted to absolute paths
        if profiler_dir and not _is_uri_path(profiler_dir):
            self.torch_profiler_dir = os.path.abspath(os.path.expanduser(profiler_dir))

        return self