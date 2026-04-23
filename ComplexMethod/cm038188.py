def forward(
        self,
        vision_features_packed: torch.Tensor,
        spatial_shapes: torch.Tensor,
    ) -> torch.Tensor:
        """Project packed vision features without materializing padded tensors.

        Args:
            vision_features_packed: (total_tokens, hidden_size) packed in tile order.
            spatial_shapes: (num_tiles, 2) on CPU (height, width) per tile.

        Returns:
            projected_packed: (total_projected_tokens, text_hidden_size)
        """
        assert spatial_shapes.device.type == "cpu", (
            "Expected `spatial_shapes` on CPU to avoid device-to-host sync in "
            "variable-length packing."
        )
        factor = self.factor
        device = vision_features_packed.device
        hidden_size = vision_features_packed.shape[-1]

        spatial_shapes_list: list[list[int]] = spatial_shapes.tolist()
        lengths_list = [h * w for h, w in spatial_shapes_list]

        gather_idx_parts: list[torch.Tensor] = []
        offset = 0

        dh = torch.arange(factor, dtype=torch.int64)
        dw = torch.arange(factor, dtype=torch.int64)
        dh_grid, dw_grid = torch.meshgrid(dh, dw, indexing="ij")
        dh_flat = dh_grid.reshape(-1)
        dw_flat = dw_grid.reshape(-1)

        for (height, width), length in zip(spatial_shapes_list, lengths_list):
            if length <= 0:
                continue
            if height % factor != 0 or width % factor != 0:
                raise ValueError(
                    "spatial_shapes must be divisible by downsample_factor: "
                    f"got ({height}, {width}) with factor={factor}."
                )
            height_out = height // factor
            width_out = width // factor

            rows_out = torch.arange(height_out, dtype=torch.int64)
            cols_out = torch.arange(width_out, dtype=torch.int64)
            rr, cc = torch.meshgrid(rows_out, cols_out, indexing="ij")
            rr = rr.reshape(-1)
            cc = cc.reshape(-1)

            token_idx = (rr[:, None] * factor + dh_flat[None, :]) * width + (
                cc[:, None] * factor + dw_flat[None, :]
            )
            gather_idx_parts.append(token_idx.reshape(-1) + offset)
            offset += length

        if gather_idx_parts:
            gather_idx = torch.cat(gather_idx_parts).to(device=device)
            gathered = vision_features_packed.index_select(0, gather_idx)
            unshuffled = gathered.reshape(-1, factor * factor * hidden_size)
        else:
            unshuffled = vision_features_packed.new_empty(
                (0, factor * factor * hidden_size)
            )

        if self.projector_use_layernorm:
            unshuffled = self.layer_norm(unshuffled)
        hidden_states = self.linear_1(unshuffled)
        hidden_states = self.act(hidden_states)
        projected_packed = self.linear_2(hidden_states)
        return projected_packed