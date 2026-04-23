def forward(
        self,
        curr: torch.Tensor,  # self-attention inputs
        memory: torch.Tensor,  # cross-attention inputs
        curr_pos: torch.Tensor | None = None,  # pos_enc for self-attention inputs
        memory_pos: torch.Tensor | None = None,  # pos_enc for cross-attention inputs
        num_obj_ptr_tokens: int = 0,  # number of object pointer *tokens*
    ) -> torch.Tensor:
        """Process inputs through attention layers, applying self and cross-attention with positional encoding.

        Args:
            curr (torch.Tensor): Self-attention input tensor, representing the current state.
            memory (torch.Tensor): Cross-attention input tensor, representing memory information.
            curr_pos (torch.Tensor | None): Positional encoding for self-attention inputs.
            memory_pos (torch.Tensor | None): Positional encoding for cross-attention inputs.
            num_obj_ptr_tokens (int): Number of object pointer tokens to exclude from rotary position embedding.

        Returns:
            (torch.Tensor): Processed output tensor after applying attention layers and normalization.

        Examples:
            >>> d_model = 256
            >>> layer = MemoryAttentionLayer(d_model)
            >>> attention = MemoryAttention(d_model, pos_enc_at_input=True, layer=layer, num_layers=3)
            >>> curr = torch.randn(10, 32, d_model)  # (seq_len, batch_size, d_model)
            >>> memory = torch.randn(20, 32, d_model)  # (mem_len, batch_size, d_model)
            >>> curr_pos = torch.randn(10, 32, d_model)
            >>> memory_pos = torch.randn(20, 32, d_model)
            >>> output = attention(curr, memory, curr_pos, memory_pos)
            >>> print(output.shape)
            torch.Size([10, 32, 256])
        """
        if isinstance(curr, list):
            assert isinstance(curr_pos, list)
            assert len(curr) == len(curr_pos) == 1
            curr, curr_pos = curr[0], curr_pos[0]

        assert curr.shape[1] == memory.shape[1], "Batch size must be the same for curr and memory"

        output = curr
        if self.pos_enc_at_input and curr_pos is not None:
            output = output + 0.1 * curr_pos

        if self.batch_first:
            # Convert to batch first
            output = output.transpose(0, 1)
            curr_pos = curr_pos.transpose(0, 1)
            memory = memory.transpose(0, 1)
            memory_pos = memory_pos.transpose(0, 1)

        for layer in self.layers:
            kwds = {}
            if isinstance(layer.cross_attn_image, RoPEAttention):
                kwds = {"num_k_exclude_rope": num_obj_ptr_tokens}

            output = layer(
                tgt=output,
                memory=memory,
                pos=memory_pos,
                query_pos=curr_pos,
                **kwds,
            )
        normed_output = self.norm(output)

        if self.batch_first:
            # Convert back to seq first
            normed_output = normed_output.transpose(0, 1)
            curr_pos = curr_pos.transpose(0, 1)

        return normed_output