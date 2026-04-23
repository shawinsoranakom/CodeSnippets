def forward_embeddings(
        self,
        xs_pad: torch.Tensor,
        masks: torch.Tensor,
        chunk_size_nc: int | list[int] | None = None,
        left_chunk_nc: int | list[int] | None = None,
    ) -> (
        tuple[
            torch.Tensor,
            torch.Tensor | None,
            torch.Tensor | None,
            torch.Tensor,
            torch.Tensor,
        ]
        | tuple[
            torch.Tensor,
            torch.Tensor | None,
            torch.Tensor | None,
            torch.Tensor,
            torch.Tensor,
            torch.Tensor,
        ]
    ):
        """Forwarding the inputs through the top embedding layers

        Args:
            xs_pad: torch.Tensor
                input tensor
            masks: torch.Tensor
                input mask
            chunk_size_nc: (optional, default is None) chunk size for
                            non-causal layers
            left_chunk_nc: (optional, default is None) # of left chunks for
                            non-causal layers
        """
        # pylint: disable=R0915
        # get new lens.
        seq_len = int(self.compute_lens_change(xs_pad.shape[1]))
        if seq_len <= 0:
            raise ValueError(
                f"""The sequence length after time reduction is invalid: 
                {seq_len}. Your input feature is too short. Consider 
                filtering out the very short sentence from data 
                loader""",
            )

        batch_size = xs_pad.shape[0]

        enc_streaming_mask = self._streaming_mask(
            seq_len, batch_size, self.chunk_size, self.left_chunk
        )
        device = xs_pad.device
        enc_streaming_mask = enc_streaming_mask.to(device)
        xs_pad = xs_pad.to(device)

        input_tensor = xs_pad
        input_tensor, masks = self._forward_embeddings_core(input_tensor, masks)

        streaming_mask = enc_streaming_mask
        if streaming_mask is not None and masks is not None:
            hs_mask = masks & streaming_mask
        elif masks is not None:
            hs_mask = masks
        else:
            hs_mask = streaming_mask

        if chunk_size_nc is not None:
            enc_streaming_mask_nc = self._streaming_mask(
                seq_len, batch_size, chunk_size_nc, left_chunk_nc
            )
            if device.type != "cpu":
                enc_streaming_mask_nc = enc_streaming_mask_nc.to(device)
            if masks is not None:
                hs_mask_nc = masks & enc_streaming_mask_nc
            else:
                hs_mask_nc = enc_streaming_mask_nc
        else:
            hs_mask_nc = None

        pos_k, pos_v = self._position_embedding(input_tensor)

        if chunk_size_nc is None:
            return input_tensor, pos_k, pos_v, hs_mask, masks
        return input_tensor, pos_k, pos_v, hs_mask, masks, hs_mask_nc