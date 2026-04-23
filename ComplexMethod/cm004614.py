def forward(self, hidden_states: torch.Tensor, mask: torch.Tensor | None, **kwargs):
        hidden_states = self.encoder_embedding(hidden_states)
        hidden_states, hs_mask, mask = self.forward_embeddings(hidden_states, mask)

        unfolded = False
        bs, seq_len, _ = hidden_states.shape
        max_seq_len = 500  # maximum position for absolute positional encoding
        if seq_len > max_seq_len:
            # audio sequence is longer than max_seq_len, unfold it into chunks of max_seq_len
            unfolded = True
            # the unfold op will drop residual frames, pad it to the multiple of max_seq_len
            if seq_len % max_seq_len > 0:
                chunk_pad_size = max_seq_len - (seq_len % max_seq_len)
            else:
                chunk_pad_size = 0
            if chunk_pad_size > 0:
                hidden_states_pad = F.pad(hidden_states, (0, 0, 0, chunk_pad_size), "constant", 0)
                hidden_states = hidden_states_pad.to(hidden_states.device)

            hidden_states = unfold_tensor(hidden_states, max_seq_len)
            masks_unfold = None
            if mask is not None:
                # revise hs_mask here because the previous calculated hs_mask did not consider extra pad
                subsampled_pad_mask = mask.squeeze(1)  # [bz, subsampled_unmask_seq_len]
                extra_padded_subsamlped_pad_mask = F.pad(
                    subsampled_pad_mask, (0, chunk_pad_size), "constant", False
                )  # extra padding to the pad mask
                extra_padded_subsamlped_pad_mask = extra_padded_subsamlped_pad_mask.unsqueeze(-1).float()
                masks_unfold = unfold_tensor(
                    extra_padded_subsamlped_pad_mask, max_seq_len
                )  # unfold the pad mask like we did to the input tensor
                masks_unfold = masks_unfold.squeeze(-1).bool()  # unfold op does not support bool tensor
            hs_mask = self.calculate_hs_mask(
                hidden_states, hidden_states.device, masks_unfold
            )  # calculate hs_mask based on the unfolded pad mask

        relative_attention_bias = self.relative_attention_bias_layer(hidden_states)
        attention_mask = hs_mask.unsqueeze(1) + relative_attention_bias

        for layer in self.encoders:
            hidden_states = layer(hidden_states, attention_mask)

        if unfolded:
            embed_dim = hidden_states.shape[-1]
            hidden_states = hidden_states.reshape(bs, -1, embed_dim)
            # if we ever padded before unfolding, we need to remove the padding
            if chunk_pad_size > 0:
                hidden_states = hidden_states[:, :-chunk_pad_size, :]

        return hidden_states