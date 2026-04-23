def _build_decode(
        self,
        block_table_tensor: torch.Tensor,
        seq_lens_device: torch.Tensor,
        max_seq_len: int,
        query_start_loc_cpu: torch.Tensor,
        query_start_loc_device: torch.Tensor,
        num_decode_tokens: int,
        dcp_tot_seq_lens_device: torch.Tensor | None,
    ) -> FlashAttnMLADecodeMetadata:
        query_lens_cpu = query_start_loc_cpu[1:] - query_start_loc_cpu[:-1]
        max_query_len = query_lens_cpu.max().item()

        # For Flash Attention MLA + full cudagraph
        max_num_splits = 0
        if (
            self.use_full_cuda_graph
            and self.max_cudagraph_size is not None
            and num_decode_tokens <= self.max_cudagraph_size
        ):
            # NOTE(woosuk): Setting num_splits > 1 may increase the memory
            # usage, because the intermediate buffers of size [num_splits,
            # num_heads, num_tokens, head_size] are allocated. Therefore,
            # we only set num_splits when using cuda graphs.
            max_num_splits = self.max_num_splits

        if envs.VLLM_BATCH_INVARIANT:
            max_num_splits = 1

        scheduler_metadata = self._schedule_decode(
            num_reqs=seq_lens_device.shape[0],
            cu_query_lens=query_start_loc_device,
            max_query_len=max_query_len,
            seqlens=seq_lens_device,
            max_seq_len=max_seq_len,
            causal=True,
            max_num_splits=max_num_splits,
        )

        if self.use_full_cuda_graph and scheduler_metadata is not None:
            n = scheduler_metadata.shape[0]
            # Ensure the persistent buffer is large enough
            assert n <= self.scheduler_metadata.shape[0], (
                f"Scheduler metadata size {n} exceeds buffer size "
                f"{self.scheduler_metadata.shape[0]}"
            )
            self.scheduler_metadata[:n] = scheduler_metadata
            # NOTE(woosuk): We should zero out the rest of the scheduler
            # metadata to guarantee the correctness. Otherwise, some thread
            # blocks may use the invalid scheduler metadata and overwrite the
            # output buffer.
            self.scheduler_metadata[n:] = 0
            scheduler_metadata = self.scheduler_metadata[:n]

        metadata = FlashAttnMLADecodeMetadata(
            block_table=block_table_tensor,
            seq_lens=seq_lens_device,
            query_start_loc=query_start_loc_device,
            max_query_len=max_query_len,
            max_seq_len=max_seq_len,
            scheduler_metadata=scheduler_metadata,
            max_num_splits=max_num_splits,
            dcp_tot_seq_lens=dcp_tot_seq_lens_device,
        )
        return metadata