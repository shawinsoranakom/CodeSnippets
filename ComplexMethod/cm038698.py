def _validate_parallel_config(self) -> Self:
        if self._api_process_rank >= self._api_process_count:
            raise ValueError(
                "Invalid value of `_api_process_rank`. "
                f"Expected to be `-1` or `[0, {self._api_process_count})`, "
                f"but found: {self._api_process_rank}"
            )

        if self.all2all_backend in ["pplx", "naive"]:
            logger.warning(
                "The '%s' all2all backend has been removed. "
                "Falling back to 'allgather_reducescatter'.",
                self.all2all_backend,
            )
            self.all2all_backend = "allgather_reducescatter"

        if self.data_parallel_size_local > self.data_parallel_size:
            raise ValueError(
                f"data_parallel_size_local ({self.data_parallel_size_local}) "
                f"must be <= data_parallel_size ({self.data_parallel_size})"
            )

        if self.data_parallel_size <= 1 and self.data_parallel_external_lb:
            raise ValueError(
                "data_parallel_external_lb can only be set when data_parallel_size > 1"
            )

        if not self.numa_bind and (
            self.numa_bind_nodes is not None or self.numa_bind_cpus is not None
        ):
            raise ValueError(
                "numa_bind_nodes and numa_bind_cpus require numa_bind=True."
            )

        if self.enable_eplb:
            if not current_platform.is_cuda_alike():
                raise ValueError(
                    "Expert parallelism load balancing is only supported on "
                    "CUDA devices or ROCm devices now."
                )
            if not self.enable_expert_parallel:
                raise ValueError("enable_expert_parallel must be True to use EPLB.")
            if self.tensor_parallel_size * self.data_parallel_size <= 1:
                raise ValueError(
                    "EPLB requires tensor_parallel_size or data_parallel_size "
                    f"to be greater than 1, but got "
                    f"TP={self.tensor_parallel_size},DP={self.data_parallel_size}."
                )
        else:
            if self.eplb_config.num_redundant_experts != 0:
                raise ValueError(
                    "num_redundant_experts is set to "
                    f"{self.eplb_config.num_redundant_experts} but EPLB is not "
                    "enabled. Either enable EPLB or unset "
                    "num_redundant_experts."
                )

        # Note(hc): In the current implementation of decode context
        # parallel(DCP), tp_size needs to be divisible by dcp_size,
        # because the world size does not change by dcp, it simply
        # reuses the GPUs of TP group, and split one TP group into
        # tp_size//dcp_size DCP groups.
        if self.tensor_parallel_size % self.decode_context_parallel_size != 0:
            raise ValueError(
                f"tp_size={self.tensor_parallel_size} must be divisible by"
                f"dcp_size={self.decode_context_parallel_size}."
            )

        if self.dcp_comm_backend == "a2a" and self.decode_context_parallel_size <= 1:
            raise ValueError(
                "dcp_comm_backend='a2a' requires decode_context_parallel_size > 1."
            )

        return self