def __call__(self, *args, **kwargs):
        forward_context = get_forward_context()
        batch_descriptor = forward_context.batch_descriptor
        ubatch_slices = forward_context.ubatch_slices
        cudagraph_runtime_mode = forward_context.cudagraph_runtime_mode

        # If there's no ubatching, just run the runnable object
        if ubatch_slices is None:
            # This is to account for the case where ubatching was aborted.
            # When we capture full graphs we only capture one graph per shape,
            # meaning that if we have a ubatched  cudagraph for the current
            # num_tokens, we don't have a non-ubatched one. Without this
            # check, the cudagraph wrapper will try to capture a cudagraph
            # for this shape during a normal run.
            if cudagraph_runtime_mode is CUDAGraphMode.FULL:
                assert batch_descriptor is not None
                if batch_descriptor.num_tokens in self.cudagraphs:
                    cudagraph_runtime_mode = CUDAGraphMode.NONE

            if cudagraph_runtime_mode in (CUDAGraphMode.NONE, CUDAGraphMode.PIECEWISE):
                return self.runnable(*args, **kwargs)
            else:
                assert self.cudagraph_wrapper is not None
                return self.cudagraph_wrapper(*args, **kwargs)

        attn_metadata = forward_context.attn_metadata
        slot_mapping = forward_context.slot_mapping
        num_tokens = sum(ubatch_slice.num_tokens for ubatch_slice in ubatch_slices)
        input_ids = kwargs["input_ids"]
        positions = kwargs["positions"]
        intermediate_tensors = kwargs["intermediate_tensors"]
        inputs_embeds = kwargs["inputs_embeds"]
        compute_stream = torch.cuda.current_stream()

        dp_metadata = forward_context.dp_metadata

        # We shouldn't be here unless we are running with multiple DP ranks
        assert dp_metadata is not None
        ubatch_dp_metadata = []
        for ubatch_slice in ubatch_slices:
            dp_size = self.vllm_config.parallel_config.data_parallel_size
            ubatch_num_tokens_across_dp = torch.tensor(
                [ubatch_slice.num_tokens] * dp_size, device="cpu", dtype=torch.int32
            )
            ubatch_dp_metadata.append(
                DPMetadata.make(
                    self.vllm_config.parallel_config,
                    ubatch_slice.num_tokens,
                    ubatch_num_tokens_across_dp,
                )
            )

        if (
            num_tokens not in self.cudagraphs
            and cudagraph_runtime_mode is CUDAGraphMode.FULL
        ):
            ubatch_metadata = self._make_ubatch_metadata(
                ubatch_slices=ubatch_slices,
                attn_metadata=attn_metadata,
                slot_mapping=slot_mapping,
                input_ids=input_ids,
                positions=positions,
                intermediate_tensors=intermediate_tensors,
                inputs_embeds=inputs_embeds,
                compute_stream=compute_stream,
                dp_metadata=ubatch_dp_metadata,
                batch_descriptor=batch_descriptor,
                cudagraph_runtime_mode=CUDAGraphMode.NONE,
            )
            with self.sm_control:
                return self._capture_ubatches(ubatch_metadata, self.runnable)
        elif (
            num_tokens in self.cudagraphs
            and cudagraph_runtime_mode is CUDAGraphMode.FULL
        ):
            cudagraph_metadata = self.cudagraphs[num_tokens]
            # Sync offloader before replay - ensures any external dependencies
            # from pre-capture prefetches are satisfied.
            get_offloader().sync_prev_onload()
            cudagraph_metadata.cudagraph.replay()
            return cudagraph_metadata.outputs
        else:
            ubatch_metadata = self._make_ubatch_metadata(
                ubatch_slices=ubatch_slices,
                attn_metadata=attn_metadata,
                slot_mapping=slot_mapping,
                input_ids=input_ids,
                positions=positions,
                intermediate_tensors=intermediate_tensors,
                inputs_embeds=inputs_embeds,
                compute_stream=compute_stream,
                dp_metadata=ubatch_dp_metadata,
                batch_descriptor=batch_descriptor,
                cudagraph_runtime_mode=CUDAGraphMode.NONE,
            )
            with self.sm_control:
                return self._run_ubatches(ubatch_metadata, self.runnable)