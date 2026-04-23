def _setup_static_tensors(self, logit_processor: ContinuousBatchingLogitsProcessorList) -> None:
        """Allocates static tensors for generation inputs and outputs. This is called only once at init time, to avoid
        repeated allocations and enable CUDA graphs. All tensors are allocated with maximum possible sizes.
        The allocated tensors are:

        - `_bulk_input_tensor`: Storage for all the small inputs: `input_ids`, `position_ids`, `cumulative_seqlens_q`,
          `logits_indices`, `cumulative_seqlens_k`, `carry_over_ids`.
        - `attention_mask`: Optional attention masks (only for eager/SDPA implementations)
        - `write_index` and `read_index` storage: Cache indexing tensors for each attention group
        - `output_ids`: Storage for generated token IDs and maybe log probabilities if return_logprobs is True
        """
        num_groups = self.cache.num_groups
        max_batch_tokens = self.cache.max_batch_tokens
        num_pages = self.cache.num_blocks * self.cache.block_size
        # Pin memory on CPU only when an accelerator is available, to speed up H2D transfers
        pin_memory = self.device.type == "cpu" and len(get_available_devices()) > 1

        # Small inputs are allocated as slices in a larget tensor aligned to 128 bytes (32 * 4b). This reduces the
        # reduces fragmentation, so it lowers the number of D2H transfers and speeds up transfers.
        bulk_lines = self.static_inputs + logit_processor.tensors_required
        bulk_columns = aligned_divide(max_batch_tokens + 1, 1, 32)
        self._bulk_input_tensor = torch.empty(
            (bulk_lines, bulk_columns), dtype=torch.int32, device=self.device, pin_memory=pin_memory
        )
        # Prepare a tensor to hold the default values for the logits processors
        self.logits_processors_defaults = torch.empty(
            (logit_processor.tensors_required, 1), dtype=torch.int32, device=self.device
        )
        logit_processor.fill_defaults(self.logits_processors_defaults)

        self.input_ids = self._bulk_input_tensor[0, :max_batch_tokens]
        self.position_ids = self._bulk_input_tensor[1, :max_batch_tokens]
        self.cumulative_seqlens_q = self._bulk_input_tensor[2, : max_batch_tokens + 1]
        self.logits_indices = self._bulk_input_tensor[3, :max_batch_tokens]
        full_attention_cumulative_seqlens_k = self._bulk_input_tensor[4, : max_batch_tokens + 1]
        sliding_attention_cumulative_seqlens_k = self._bulk_input_tensor[5, : max_batch_tokens + 1]
        self.carry_over_ids = self._bulk_input_tensor[6, :max_batch_tokens]  # only used for async API

        # For sequence length of KV, the entries in the dict depend on the model
        self.cumulative_seqlens_k: dict[str, torch.Tensor] = {}
        if self.cache.num_full_attention_groups:
            self.cumulative_seqlens_k["full_attention"] = full_attention_cumulative_seqlens_k
        if self.cache.num_sliding_attention_groups:
            self.cumulative_seqlens_k["sliding_attention"] = sliding_attention_cumulative_seqlens_k

        # Output tensor and scalars
        num_output_rows = 2 if self.return_logprobs else 1
        self.output_ids = torch.empty(
            (num_output_rows, max_batch_tokens + 1), dtype=torch.int32, device=self.device, pin_memory=pin_memory
        )
        # Last output token is never changed and set to 0 for async carry on purpose
        self.output_ids.zero_()
        self.total_seqlen_q = 0
        self.max_seqlen_q = 0
        self.max_seqlen_k = dict.fromkeys(self.cumulative_seqlens_k.keys(), 0)

        # If the attention mask is needed, it is allocated separately
        if attn_mask_is_needed(self.config):
            self.attention_mask = {}
            for layer_type in self.cumulative_seqlens_k.keys():
                self.attention_mask[layer_type] = torch.empty(
                    size=(1, 1, max_batch_tokens, num_pages + max_batch_tokens),
                    dtype=self.model_dtype,
                    device=self.device,
                    pin_memory=pin_memory,
                )
        else:
            self.attention_mask = None

        # No block table == No elements in the block table tensor
        n = num_groups if self.cache.max_blocks_per_request > 0 else 0
        self.block_table = torch.empty(
            (n, max_batch_tokens, self.cache.max_blocks_per_request),
            dtype=torch.int32,
            device=self.device,
            pin_memory=pin_memory,
        )

        # For other kwargs, we need a list of tensors with as many tensors as there are groups
        self.write_index_storage = torch.empty(
            (num_groups, max_batch_tokens), dtype=torch.int64, device=self.device, pin_memory=pin_memory
        )
        self.read_index_storage = torch.empty(
            (num_groups, num_pages + max_batch_tokens), dtype=torch.int64, device=self.device, pin_memory=pin_memory
        )