def _update_metadata_for_cudagraph_capture(
        self,
        metadata: M,
    ) -> M:
        """
        Update the metadata for cudagraph capture.
        Currently, only decode is supported for full cudagraphs with Mamba.
        """
        state_indices_tensor_d = metadata.state_indices_tensor_d
        query_start_loc_d = metadata.query_start_loc_d
        num_accepted_tokens = metadata.num_accepted_tokens
        block_idx_last_scheduled_token = metadata.block_idx_last_scheduled_token
        block_idx_last_computed_token = metadata.block_idx_last_computed_token
        if (
            metadata.num_prefills == 0
            and metadata.num_decodes <= self.decode_cudagraph_max_bs
            and self.compilation_config.cudagraph_mode.has_full_cudagraphs()
        ):
            padded_bs = metadata.num_reqs
            self.state_indices_tensor_d[: metadata.num_decodes].copy_(
                state_indices_tensor_d, non_blocking=True
            )
            state_indices_tensor_d = self.state_indices_tensor_d[:padded_bs]
            state_indices_tensor_d[metadata.num_decodes :] = NULL_BLOCK_ID

            if self.use_spec_decode and num_accepted_tokens is not None:
                assert query_start_loc_d is not None
                query_start_loc_d = query_start_loc_d[: padded_bs + 1]
                self.decode_num_accepted_tokens[: metadata.num_decodes].copy_(
                    num_accepted_tokens, non_blocking=True
                )
                num_accepted_tokens = self.decode_num_accepted_tokens[:padded_bs]
                num_accepted_tokens[metadata.num_decodes :] = (
                    1  # pad with 1st slot index
                )

            if self.vllm_config.cache_config.mamba_cache_mode == "all":
                assert block_idx_last_scheduled_token is not None
                assert block_idx_last_computed_token is not None
                self.block_idx_last_scheduled_token[: metadata.num_decodes].copy_(
                    block_idx_last_scheduled_token[: metadata.num_decodes],
                    non_blocking=True,
                )
                block_idx_last_scheduled_token = self.block_idx_last_scheduled_token[
                    : metadata.num_decode_tokens
                ]

                self.block_idx_last_computed_token[: metadata.num_decodes].copy_(
                    block_idx_last_computed_token[: metadata.num_decodes],
                    non_blocking=True,
                )
                block_idx_last_computed_token = self.block_idx_last_computed_token[
                    : metadata.num_decode_tokens
                ]

        return replace(
            metadata,
            state_indices_tensor_d=state_indices_tensor_d,
            query_start_loc_d=query_start_loc_d,
            num_accepted_tokens=num_accepted_tokens,
            block_idx_last_scheduled_token=block_idx_last_scheduled_token,
            block_idx_last_computed_token=block_idx_last_computed_token,
        )