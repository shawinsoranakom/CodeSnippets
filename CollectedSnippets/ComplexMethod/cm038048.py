def select_encoder_cudagraph_items(
        self,
        mm_kwargs: dict[str, Any],
        indices: list[int],
    ) -> dict[str, Any]:
        grid_thw = self._get_grid_thw_by_modality(mm_kwargs)
        pixel_values = self._get_pixel_values_by_modality(mm_kwargs)

        if len(indices) == 0:
            if self.get_input_modality(mm_kwargs) == "image":
                return {
                    "pixel_values": pixel_values[:0],
                    "image_grid_thw": [],
                }
            else:
                return {
                    "pixel_values_videos": pixel_values[:0],
                    "video_grid_thw": [],
                }

        # Compute cumulative patch offsets for slicing pixel_values
        patches_per_item = [t * h * w for t, h, w in grid_thw]
        cum_patches = [0]
        for p in patches_per_item:
            cum_patches.append(cum_patches[-1] + p)

        selected_pv = torch.cat(
            [pixel_values[cum_patches[i] : cum_patches[i + 1]] for i in indices]
        )
        selected_grid = [grid_thw[i] for i in indices]

        if self.get_input_modality(mm_kwargs) == "image":
            return {
                "pixel_values": selected_pv,
                "image_grid_thw": selected_grid,
            }
        else:
            return {
                "pixel_values_videos": selected_pv,
                "video_grid_thw": selected_grid,
            }