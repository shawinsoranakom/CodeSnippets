def compute_3d_position_ids(
        self,
        input_ids: torch.Tensor | None,
        image_grid_thw: torch.Tensor | None,
        images_per_sample: torch.Tensor | None,
        inputs_embeds: torch.Tensor | None,
        attention_mask: torch.Tensor | None,
        past_key_values: torch.Tensor | None,
    ) -> torch.Tensor | None:
        past_key_values_length = 0 if past_key_values is None else past_key_values.get_seq_length()
        can_compute_mrope = input_ids is not None and image_grid_thw is not None

        if can_compute_mrope and (self.rope_deltas is None or past_key_values_length == 0):
            position_ids, rope_deltas = self.get_rope_index(
                input_ids,
                image_grid_thw=image_grid_thw,
                attention_mask=attention_mask,
                images_per_sample=images_per_sample,
            )
            self.rope_deltas = rope_deltas
        # Use pre-calculated rope-deltas to infer correct 3D position ids during incremental
        # generation (past_key_values_length > 0) or when only inputs_embeds is provided (no input_ids
        # to recompute from). Skip when input_ids is provided without past_key_values to avoid shape
        # mismatches from stale rope_deltas (e.g., training forward pass after generation).
        elif self.rope_deltas is not None and (past_key_values_length > 0 or input_ids is None):
            batch_size, seq_length, _ = inputs_embeds.shape
            if self._cached_decode_position_ids is not None:
                step = past_key_values_length - self._prefill_len
                position_ids = self._cached_decode_position_ids[:, :, step : step + seq_length].permute(1, 0, 2)
            else:
                position_ids = (
                    torch.arange(inputs_embeds.shape[1], device=inputs_embeds.device) + past_key_values_length
                )
                position_ids = position_ids.view(1, 1, -1).repeat(3, batch_size, 1)
        else:
            # Can't build correct 3D positions. Let the model infer it
            position_ids = None
        return position_ids