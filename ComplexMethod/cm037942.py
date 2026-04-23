def forward(
        self, xs_pad: torch.Tensor, masks: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Conformer Forward function

        Args:
            xs_pad: torch.Tensor
                input tensor
            masks: torch.Tensor
                post-embedding input lengths
        """
        xs_pad = self.encoder_embedding(xs_pad)
        input_tensor, pos_k, pos_v, hs_mask, masks = self.forward_embeddings(
            xs_pad, masks
        )

        unfolded = False
        ori_bz, seq_len, D = input_tensor.shape
        max_seq_len = 500  # maximum position for absolute positional encoding
        if seq_len > max_seq_len:
            # audio sequence is longer than max_seq_len, unfold it into chunks
            # of max_seq_len
            unfolded = True
            # the unfold op will drop residual frames, pad it to the multiple
            # of max_seq_len
            if seq_len % max_seq_len > 0:
                chunk_pad_size = max_seq_len - (seq_len % max_seq_len)
            else:
                chunk_pad_size = 0
            if chunk_pad_size > 0:
                input_tensor_pad = F.pad(
                    input_tensor, (0, 0, 0, chunk_pad_size), "constant", 0
                )
                input_tensor = input_tensor_pad.to(input_tensor.device)
            input_tensor = unfold_tensor(input_tensor, max_seq_len)
            if masks is not None:
                # revise hs_mask here because the previous calculated hs_mask
                # did not consider extra pad
                subsampled_pad_mask = masks.squeeze(
                    1
                )  # [bz, subsampled_unmask_seq_len]
                extra_padded_subsamlped_pad_mask = F.pad(
                    subsampled_pad_mask, (0, chunk_pad_size), "constant", False
                )  # extra padding to the pad mask
                extra_padded_subsamlped_pad_mask = (
                    extra_padded_subsamlped_pad_mask.unsqueeze(-1).float()
                )
                masks_unfold = unfold_tensor(
                    extra_padded_subsamlped_pad_mask, max_seq_len
                )  # unfold the pad mask like we did to the input tensor
                masks_unfold = masks_unfold.squeeze(
                    -1
                ).bool()  # unfold op does not support bool tensor
            else:
                masks_unfold = None
            hs_mask = self.calculate_hs_mask(
                input_tensor, input_tensor.device, masks_unfold
            )  # calculate hs_mask based on the unfolded pad mask

        # layer_emb = None

        relative_attention_bias = self.init_relative_attention_bias(input_tensor)

        _simplified_path = (
            self.extra_layer_output_idx == -1 and relative_attention_bias is None
        )

        if _simplified_path:
            input_tensor, *_ = self.encoders(input_tensor, pos_k, pos_v, hs_mask)
        else:
            for i, layer in enumerate(self.encoders):
                input_tensor, _, _, _ = layer(
                    input_tensor,
                    pos_k,
                    pos_v,
                    hs_mask,
                    relative_attention_bias=relative_attention_bias,
                )

                # if i == self.extra_layer_output_idx:
                #     layer_emb = input_tensor

        if unfolded:
            embed_dim = input_tensor.shape[-1]
            input_tensor = input_tensor.reshape(ori_bz, -1, embed_dim)
            # if we ever padded before unfolding, we need to remove the padding
            if chunk_pad_size > 0:
                input_tensor = input_tensor[:, :-chunk_pad_size, :]

        return input_tensor, masks