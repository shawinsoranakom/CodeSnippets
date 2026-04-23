def select_encoder_cudagraph_items(
        self, mm_kwargs: dict[str, Any], indices: list[int]
    ) -> dict[str, Any]:
        modality = self.get_input_modality(mm_kwargs)
        pv_key = "pixel_values_videos" if modality == "video" else "pixel_values"
        grid_key = "video_grid_thw" if modality == "video" else "image_grid_thw"

        grid_thw = self._get_grid_thw(mm_kwargs)
        pixel_values = self._get_pixel_values(mm_kwargs)

        if len(indices) == 0:
            return {pv_key: pixel_values[:0], grid_key: []}

        patches_per_item = [t * h * w for t, h, w in grid_thw]
        cum_patches = [0]
        for p in patches_per_item:
            cum_patches.append(cum_patches[-1] + p)

        selected_pv = torch.cat(
            [pixel_values[cum_patches[i] : cum_patches[i + 1]] for i in indices]
        )
        return {pv_key: selected_pv, grid_key: [grid_thw[i] for i in indices]}