def _reset_static_tensors(self, full_reset: bool = False) -> None:
        """Reset static tensors for the next batch. For efficiency, this only resets the portions of tensors that were
        actually used in the previous batch, using the attributes num_q_tokens and max_kv_read. If a (full_reset)
        is requested, the entire tensor storage is reset.
        """
        # Compute the slice to reset
        q_len = self.write_index_storage.size(-1) if full_reset else self.num_q_tokens
        kv_len = self.read_index_storage.size(-1) if full_reset else self.max_kv_read

        # Reset the attributes part of the bulk input tensor in one kernel
        self._bulk_input_tensor[: self.static_inputs, : q_len + 1].zero_()
        if full_reset:
            self._bulk_input_tensor[self.static_inputs :] = self.logits_processors_defaults
        self.max_seqlen_q = 0

        # Reset the logits indices and output ids
        self.logits_indices[:q_len].zero_()
        self.output_ids[:, :q_len].zero_()

        # Reset the attributes that are either tensors or dict of tensors
        for layer_type in self.cumulative_seqlens_k:
            self.max_seqlen_k[layer_type] = 0
            if self.attention_mask is not None:
                self.attention_mask[layer_type][:, :, :q_len, : q_len + kv_len].fill_(
                    torch.finfo(self.model_dtype).min
                )

        # If this is a full reset, we reset every tensors
        if full_reset:
            self.block_table[:, :q_len].fill_(-1)
            self.write_index_storage[:, :q_len].fill_(self._trash_index)
            self.read_index_storage[:, : q_len + kv_len].fill_(self._trash_index)
        # If this is not a full reset, and we are going to use the block table, we only reset it
        elif self.use_block_table:
            self.block_table[:, :q_len].fill_(-1)
        # Otherwise, the read and write indices are the ones used, so we reset them
        else:
            self.write_index_storage[:, :q_len].fill_(self._trash_index)
            self.read_index_storage[:, : q_len + kv_len].fill_(self._trash_index)