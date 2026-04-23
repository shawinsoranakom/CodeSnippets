def _get_all_layer_features(
        self,
        pixel_values: torch.Tensor,
        image_sizes: torch.Tensor,
    ) -> tuple[list[int], list[torch.Tensor]]:
        """Extract deepstack + spatial features for all levels.

        Returns:
          llm_layer_indices: ordered list of target LLM layer indices
          per_image_packed:  one tensor per image, shape
                             (num_tokens_i, lm_hidden_size * num_levels),
                             all levels packed on dim=-1.

        Packing on dim=-1 means the framework's token-level slicing for
        chunked prefill preserves all levels intact.
        """
        select_strategy = self._vision_feature_select_strategy

        image_num_patches = [
            image_size_to_num_patches(
                image_size=imsize,
                grid_pinpoints=self.config.image_grid_pinpoints,
                patch_size=self.config.vision_config.image_size,
            )
            for imsize in image_sizes
        ]

        if pixel_values.dim() == 5:
            pixel_values = torch.cat(
                [pv[:np_] for pv, np_ in zip(pixel_values, image_num_patches)],
                dim=0,
            )

        all_hidden_states = self._get_vision_hidden_states(pixel_values)

        # Collect per-level: (llm_layer, [per_image_tensor, ...])
        levels: list[tuple[int, list[torch.Tensor]]] = []

        for proj_idx, (vision_layer, llm_layer) in enumerate(self._deepstack_layer_map):
            selected = all_hidden_states[vision_layer]
            if select_strategy == "default":
                selected = selected[:, 1:]
            projected = self.layerwise_projectors[proj_idx](selected)
            per_image = self._pack_and_unpad_image_features(
                torch.split(projected, image_num_patches, dim=0), image_sizes
            )
            levels.append((llm_layer, per_image))

        if self._use_spatial_sampling and self.spatial_projectors is not None:
            spatial_hidden = all_hidden_states[self._spatial_vision_layer]
            if select_strategy == "default":
                spatial_hidden = spatial_hidden[:, 1:]
            for group_idx, llm_layer in enumerate(self._spatial_target_layers):
                projected = self.spatial_projectors[group_idx](spatial_hidden)
                per_image = self._pack_and_unpad_image_features(
                    torch.split(projected, image_num_patches, dim=0), image_sizes
                )
                levels.append((llm_layer, per_image))

        llm_layer_indices = [llm_layer for llm_layer, _ in levels]
        num_images = len(image_sizes)
        per_image_packed = [
            torch.cat([levels[lvl][1][img] for lvl in range(len(levels))], dim=-1)
            for img in range(num_images)
        ]

        return llm_layer_indices, per_image_packed