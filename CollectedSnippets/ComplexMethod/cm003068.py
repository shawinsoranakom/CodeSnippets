def forward(self, sequence_state, pairwise_state, mask=None, chunk_size=None, **__kwargs):
        """
        Inputs:
          sequence_state: B x L x sequence_state_dim pairwise_state: B x L x L x pairwise_state_dim mask: B x L boolean
          tensor of valid positions

        Output:
          sequence_state: B x L x sequence_state_dim pairwise_state: B x L x L x pairwise_state_dim
        """
        if len(sequence_state.shape) != 3:
            raise ValueError(f"`sequence_state` should be a 3d-tensor, got {len(sequence_state.shape)} dims.")
        if len(pairwise_state.shape) != 4:
            raise ValueError(f"`pairwise_state` should be a 4d-tensor, got {len(pairwise_state.shape)} dims.")
        if mask is not None and len(mask.shape) != 2:
            raise ValueError(f"`mask` should be a 2d-tensor, got {len(mask.shape)} dims.")

        batch_dim, seq_dim, sequence_state_dim = sequence_state.shape
        pairwise_state_dim = pairwise_state.shape[3]

        if sequence_state_dim != self.config.sequence_state_dim:
            raise ValueError(
                "`sequence_state` last dimension should be equal to `self.sequence_state_dim`. Got "
                f"{sequence_state_dim} != {self.config.sequence_state_dim}."
            )
        if pairwise_state_dim != self.config.pairwise_state_dim:
            raise ValueError(
                "`pairwise_state` last dimension should be equal to `self.pairwise_state_dim`. Got "
                f"{pairwise_state_dim} != {self.config.pairwise_state_dim}."
            )
        if batch_dim != pairwise_state.shape[0]:
            raise ValueError(
                f"`sequence_state` and `pairwise_state` have inconsistent batch size: {batch_dim} != "
                f"{pairwise_state.shape[0]}."
            )
        if seq_dim != pairwise_state.shape[1] or seq_dim != pairwise_state.shape[2]:
            raise ValueError(
                f"`sequence_state` and `pairwise_state` have inconsistent sequence length: {seq_dim} != "
                f"{pairwise_state.shape[1]} or {pairwise_state.shape[2]}."
            )

        # Update sequence state
        bias = self.pair_to_sequence(pairwise_state)

        # Self attention with bias + mlp.
        y = self.layernorm_1(sequence_state)
        y, _ = self.seq_attention(y, mask=mask, bias=bias)
        sequence_state = sequence_state + self.drop(y)
        sequence_state = self.mlp_seq(sequence_state)

        # Update pairwise state
        pairwise_state = pairwise_state + self.sequence_to_pair(sequence_state)

        # Axial attention with triangular bias.
        tri_mask = mask.unsqueeze(2) * mask.unsqueeze(1) if mask is not None else None
        pairwise_state = pairwise_state + self.row_drop(self.tri_mul_out(pairwise_state, mask=tri_mask))
        pairwise_state = pairwise_state + self.col_drop(self.tri_mul_in(pairwise_state, mask=tri_mask))
        pairwise_state = pairwise_state + self.row_drop(
            self.tri_att_start(pairwise_state, mask=tri_mask, chunk_size=chunk_size)
        )
        pairwise_state = pairwise_state + self.col_drop(
            self.tri_att_end(pairwise_state, mask=tri_mask, chunk_size=chunk_size)
        )

        # MLP over pairs.
        pairwise_state = self.mlp_pair(pairwise_state)

        return sequence_state, pairwise_state