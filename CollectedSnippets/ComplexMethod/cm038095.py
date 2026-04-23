def forward(
        self,
        x: torch.Tensor,
        grid_thw: list[list[int]],
    ) -> torch.Tensor:
        hidden_states = x.to(device=self.device, dtype=self.dtype)
        hidden_states = self.patch_embed(hidden_states)

        if self.apply_vit_abs_pos_embed:
            pos_embeds = self.fast_pos_embed_interpolate(grid_thw)
            hidden_states = hidden_states + pos_embeds
        rotary_pos_emb_cos, rotary_pos_emb_sin = self.rot_pos_emb(grid_thw)

        # RDNA3 (gfx11) specific bug workaround: torch.repeat_interleave triggers
        # kernel crashes. We attempt the operation and catch the RuntimeError
        # to switch to a vectorized cumsum + searchsorted approach.
        try:
            cu_seqlens = torch.repeat_interleave(
                grid_thw[:, 1] * grid_thw[:, 2], grid_thw[:, 0]
            ).cumsum(
                dim=0,
                dtype=grid_thw.dtype if torch.jit.is_tracing() else torch.int32,
            )
            cu_seqlens = F.pad(cu_seqlens, (1, 0), value=0)
        except RuntimeError:
            logger.warning(
                "torch.repeat_interleave not executable, "
                "switching to vectorized searchsorted implementation."
            )
            repeat_counts = grid_thw[:, 0]
            values = grid_thw[:, 1] * grid_thw[:, 2]
            repeat_cumsum = repeat_counts.cumsum(0)
            total_items = repeat_cumsum[-1].item()

            indices = torch.searchsorted(
                repeat_cumsum,
                torch.arange(total_items, device=grid_thw.device),
                right=True,
            )
            cu_seqlens = values[indices].cumsum(
                dim=0,
                dtype=grid_thw.dtype if torch.jit.is_tracing() else torch.int32,
            )
            cu_seqlens = F.pad(cu_seqlens, (1, 0), value=0)

        hidden_states = hidden_states.unsqueeze(1)
        rotary_pos_emb_cos = rotary_pos_emb_cos.to(hidden_states.device)
        rotary_pos_emb_sin = rotary_pos_emb_sin.to(hidden_states.device)
        max_seqlen = self.compute_attn_mask_seqlen(cu_seqlens)

        # Recompute cu_seqlens in numpy from grid_thw to avoid GPU->CPU sync
        grid_thw_np = grid_thw.cpu().numpy()
        cu_seqlens_np = np.repeat(
            grid_thw_np[:, 1] * grid_thw_np[:, 2], grid_thw_np[:, 0]
        ).cumsum(axis=0, dtype=np.int32)
        cu_seqlens_np = np.concatenate([np.zeros(1, dtype=np.int32), cu_seqlens_np])
        sequence_lengths = MMEncoderAttention.maybe_compute_seq_lens(
            self.attn_backend,
            cu_seqlens_np,
            self.device,
        )

        hidden_states_list = []
        deepstack_visual_indexes = self.deepstack_visual_indexes

        for layer_num, blk in enumerate(self.blocks):
            hidden_states = blk(
                hidden_states,
                cu_seqlens=cu_seqlens,
                rotary_pos_emb_cos=rotary_pos_emb_cos,
                rotary_pos_emb_sin=rotary_pos_emb_sin,
                max_seqlen=max_seqlen,
                sequence_lengths=sequence_lengths,
            )
            if (
                deepstack_visual_indexes is not None
                and layer_num in deepstack_visual_indexes
            ):
                hidden_states_list.append(hidden_states)

        hidden_states = self.merger(hidden_states)

        # processing deepstack
        if deepstack_visual_indexes is not None:
            processed_hidden_states_list = [hidden_states]
            for idx, x in enumerate(hidden_states_list):
                x = self.merger_list[idx](x)
                processed_hidden_states_list.append(x)
            # we cat the original visual features and deepstack features
            # along the feature dim
            hidden_states = torch.cat(
                processed_hidden_states_list, dim=1
            )  # [seq_len, hidden_size * (1 + depth_of_deepstack)]

        return hidden_states