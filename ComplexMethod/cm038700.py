def _verify_args(self) -> Self:
        # Lazy import to avoid circular import
        from vllm.v1.executor import Executor

        # Enable batch invariance settings if requested
        if envs.VLLM_BATCH_INVARIANT:
            self.disable_custom_all_reduce = True

        if (
            self.distributed_executor_backend is not None
            and not isinstance(self.distributed_executor_backend, str)
            and not (
                isinstance(self.distributed_executor_backend, type)
                and issubclass(self.distributed_executor_backend, Executor)
            )
        ):
            raise ValueError(
                "Unrecognized distributed executor backend "
                f"{self.distributed_executor_backend}. Supported "
                "values are 'ray', 'mp' 'uni', 'external_launcher', "
                " custom Executor subclass or its import path."
            )
        if self.use_ray:
            from vllm.v1.executor import ray_utils

            ray_utils.assert_ray_available()

        if not current_platform.use_custom_allreduce():
            self.disable_custom_all_reduce = True
            logger.debug(
                "Disabled the custom all-reduce kernel because it is not "
                "supported on current platform."
            )
        if self.nnodes > 1:
            self.disable_custom_all_reduce = True
            logger.debug(
                "Disabled the custom all-reduce since we are running on multi-node."
            )
        if self.ray_workers_use_nsight and not self.use_ray:
            raise ValueError(
                "Unable to use nsight profiling unless workers run with Ray."
            )

        return self