def initialize_cudagraph_keys(
        self, cudagraph_mode: CUDAGraphMode, uniform_decode_query_len: int = 1
    ):
        # This should be called only after attention backend is initialized. So we can
        # get the correct cudagraph mode after backend support is resolved.
        self.cudagraph_mode = cudagraph_mode

        # Early exit if cudagraphs are disabled
        if cudagraph_mode == CUDAGraphMode.NONE:
            self.keys_initialized = True
            return

        self._compute_bs_to_padded_graph_size()

        # Get LoRA cases to capture
        lora_cases = self._get_lora_cases()
        self.captured_lora_counts = [
            lora_count for lora_count in lora_cases if lora_count
        ]

        # Note: we create all valid keys for cudagraph here but do not
        # guarantee all keys would be used. For example, if we allow lazy
        # capturing in future PR, some keys may never be triggered.
        if cudagraph_mode.mixed_mode() != CUDAGraphMode.NONE:
            assert self.compilation_config.cudagraph_capture_sizes is not None, (
                "Cudagraph capture sizes must be set when mixed mode is enabled."
            )
            for bs, num_active_loras in product(
                self.compilation_config.cudagraph_capture_sizes, lora_cases
            ):
                batch_desc = self._create_padded_batch_descriptor(
                    bs, False, num_active_loras > 0, num_active_loras
                )
                # Only relax for PIECEWISE mode. FULL mode needs exact num_reqs
                # because FA3's scheduler_metadata computation depends on it.
                if cudagraph_mode.mixed_mode() == CUDAGraphMode.PIECEWISE:
                    batch_desc = replace(batch_desc, num_reqs=None, uniform=False)
                self.add_cudagraph_key(cudagraph_mode.mixed_mode(), batch_desc)

        # if decode cudagraph mode is FULL, and we don't already have mixed
        # mode full cudagraphs then add them here.
        if (
            cudagraph_mode.decode_mode() == CUDAGraphMode.FULL
            and cudagraph_mode.separate_routine()
        ):
            max_num_tokens = (
                uniform_decode_query_len
                * self.vllm_config.scheduler_config.max_num_seqs
            )
            assert self.compilation_config.cudagraph_capture_sizes is not None, (
                "Cudagraph capture sizes must be set when full mode is enabled."
            )
            cudagraph_capture_sizes_for_decode = [
                x
                for x in self.compilation_config.cudagraph_capture_sizes
                if x <= max_num_tokens and x >= uniform_decode_query_len
            ]
            for bs, num_active_loras in product(
                cudagraph_capture_sizes_for_decode, lora_cases
            ):
                self.add_cudagraph_key(
                    CUDAGraphMode.FULL,
                    self._create_padded_batch_descriptor(
                        bs, True, num_active_loras > 0, num_active_loras
                    ),
                )

        self.keys_initialized = True