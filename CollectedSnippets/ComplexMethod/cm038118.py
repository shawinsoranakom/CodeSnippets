def forward(
        self,
        pixel_values: torch.Tensor,
        grid_thw: torch.Tensor,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
    ) -> tuple | BaseModelOutput:
        """Run the vision transformer and optionally return intermediate states.

        Unlike the base `Qwen2VisionTransformer`, this wrapper exposes the
        pre-merger patch-level representations and a HF-style `BaseModelOutput`
        so that the existing projector / abstractor code can be reused.
        """
        assert return_dict, "Only return_dict=True is supported."

        # Patchify
        x = pixel_values.to(device=self.device, dtype=self.dtype)
        x = self.patch_embed(x)  # (num_patches, embed_dim)

        # Prepare grid and rotary embeddings – mirror base implementation.
        if isinstance(grid_thw, list):
            grid_thw_list = grid_thw
            grid_thw_np = np.array(grid_thw, dtype=np.int32)
        else:
            grid_thw_list = grid_thw.tolist()
            grid_thw_np = grid_thw.cpu().numpy()

        rotary_pos_emb_cos, rotary_pos_emb_sin = self.rot_pos_emb(grid_thw_list)

        # Compute cu_seqlens in numpy then move to device, same as base model.
        cu_seqlens = np.repeat(
            grid_thw_np[:, 1] * grid_thw_np[:, 2],
            grid_thw_np[:, 0],
        ).cumsum(axis=0, dtype=np.int32)
        cu_seqlens = np.concatenate([np.zeros(1, dtype=np.int32), cu_seqlens])
        cu_seqlens = torch.from_numpy(cu_seqlens).to(
            self.device,
            non_blocking=True,
        )

        # Shape to (S, B, D) with batch dimension 1 as expected by the blocks.
        x = x.unsqueeze(1)

        # Pre-compute seqlens for attention backend.
        max_seqlen = self.compute_attn_mask_seqlen(cu_seqlens)

        encoder_states = () if output_hidden_states else None

        for blk in self.blocks:
            if output_hidden_states:
                # Store patch-level states (S, D).
                encoder_states = encoder_states + (x.squeeze(1),)

            x = blk(
                x,
                cu_seqlens=cu_seqlens,
                rotary_pos_emb_cos=rotary_pos_emb_cos,
                rotary_pos_emb_sin=rotary_pos_emb_sin,
                max_seqlen=max_seqlen,
            )

        # Final hidden state at patch level (S, D).
        hidden_states = x.squeeze(1)
        if output_hidden_states:
            encoder_states = encoder_states + (hidden_states,)

        if not return_dict:
            return tuple(v for v in [hidden_states, encoder_states] if v is not None)
        return BaseModelOutput(
            last_hidden_state=hidden_states,
            hidden_states=encoder_states,
        )