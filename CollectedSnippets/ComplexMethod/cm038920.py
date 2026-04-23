def benchmark_allreduce(
        self, sequence_length: int, num_warmup: int, num_trials: int
    ) -> dict[str, float]:
        """Benchmark allreduce operations for all available communicators."""

        results = {}

        # Define communicators with their benchmark functions
        communicators = []

        if self.custom_allreduce is not None:
            comm = self.custom_allreduce
            # CustomAllreduce one-shot
            communicators.append(
                (
                    "ca_1stage",
                    lambda t, c=comm: c.custom_all_reduce(t),
                    lambda t, c=comm: c.should_custom_ar(t),
                    comm.capture(),
                    {"VLLM_CUSTOM_ALLREDUCE_ALGO": "1stage"},
                    None,  # no destroy function
                )
            )
            # CustomAllreduce two-shot
            communicators.append(
                (
                    "ca_2stage",
                    lambda t, c=comm: c.custom_all_reduce(t),
                    lambda t, c=comm: c.should_custom_ar(t),
                    comm.capture(),
                    {"VLLM_CUSTOM_ALLREDUCE_ALGO": "2stage"},
                    None,  # no destroy function
                )
            )

        if self.pynccl_comm is not None:
            comm = self.pynccl_comm
            communicators.append(
                (
                    "pynccl",
                    lambda t, c=comm: c.all_reduce(t),
                    lambda t: True,  # Always available if initialized
                    nullcontext(),
                    {},  # no env variable needed
                    None,  # no destroy function
                )
            )
            communicators.append(
                (
                    "pynccl-symm",
                    lambda t: torch.ops.vllm.all_reduce_symmetric_with_copy(t),
                    lambda t: True,  # Always available if initialized
                    nullcontext(),
                    {},  # no env variable needed
                    None,  # no destroy function
                )
            )

        if self.symm_mem_comm_multimem is not None:
            comm = self.symm_mem_comm_multimem
            communicators.append(
                (
                    "symm_mem_multimem",
                    lambda t, c=comm: c.all_reduce(t),
                    lambda t, c=comm: c.should_use_symm_mem(t),
                    nullcontext(),
                    {},  # no env variable needed
                    None,  # no destroy function
                )
            )

        if self.symm_mem_comm_two_shot is not None:
            comm = self.symm_mem_comm_two_shot
            communicators.append(
                (
                    "symm_mem_two_shot",
                    lambda t, c=comm: c.all_reduce(t),
                    lambda t, c=comm: c.should_use_symm_mem(t),
                    nullcontext(),
                    {},  # no env variable needed
                    None,  # no destroy function needed
                )
            )

        if self.fi_ar_comm is not None:
            comm = self.fi_ar_comm
            communicators.append(
                (
                    "flashinfer_trtllm",
                    lambda t, c=comm: c.all_reduce(t),
                    lambda t, c=comm: c.should_use_fi_ar(t),
                    nullcontext(),
                    {"VLLM_FLASHINFER_ALLREDUCE_BACKEND": "trtllm"},
                    lambda c=comm: c.destroy(),
                )
            )
            communicators.append(
                (
                    "flashinfer_mnnvl",
                    lambda t, c=comm: c.all_reduce(t),
                    lambda t, c=comm: c.should_use_fi_ar(t),
                    nullcontext(),
                    {"VLLM_FLASHINFER_ALLREDUCE_BACKEND": "mnnvl"},
                    lambda c=comm: c.destroy(),
                )
            )

        # Benchmark each communicator
        for (
            name,
            allreduce_fn,
            should_use_fn,
            context,
            env_dict,
            destroy_fn,
        ) in communicators:
            # Save original values and apply new environment variables
            saved_env = {key: os.environ.get(key) for key in env_dict}
            for key, value in env_dict.items():
                os.environ[key] = value
            try:
                latency = self.benchmark_allreduce_single(
                    sequence_length,
                    allreduce_fn,
                    should_use_fn,
                    context,
                    num_warmup,
                    num_trials,
                )
                if latency is not None:
                    results[name] = latency
            finally:
                if destroy_fn is not None:
                    destroy_fn()
                # Restore environment variables to their original state
                for key, original_value in saved_env.items():
                    if original_value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = original_value

        return results