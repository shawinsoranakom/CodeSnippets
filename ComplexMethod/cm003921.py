def _preprocess(
        self,
        images: list["torch.Tensor"],
        do_normalize: bool,
        max_patches: int,
        patch_size: SizeDict,
        disable_grouping: bool | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> BatchFeature:
        width, height, rows, cols, attention_masks = [], [], [], [], []
        obj_idx_to_new_index_map = {}
        current_index = -1

        # Group images by size for batched resizing
        processed_image_patches_grouped = {}
        grouped_images, grouped_images_index = group_images_by_shape(images, disable_grouping=disable_grouping)
        for shape, stacked_images in grouped_images.items():
            if do_normalize:
                stacked_images = self.normalize(stacked_images, **kwargs)

            patches, resized_width, resized_height, n_rows, n_columns = self.extract_flattened_patches(
                image=stacked_images,
                max_patches=max_patches,
                patch_size=patch_size,
            )
            n_of_stacked_images = stacked_images.size()[0]
            width.extend([resized_width] * n_of_stacked_images)
            height.extend([resized_height] * n_of_stacked_images)
            rows.extend([n_rows] * n_of_stacked_images)
            cols.extend([n_columns] * n_of_stacked_images)
            # create attention mask
            attention_masks.extend(list((patches.sum(axis=-1) != 0).to(dtype=torch.float32)))
            processed_image_patches_grouped[shape] = list(patches)
            for x in processed_image_patches_grouped[shape]:
                current_index += 1
                obj_idx_to_new_index_map[id(x)] = current_index

        processed_images = reorder_images(processed_image_patches_grouped, grouped_images_index)
        orig_idx_to_new_idx_map = {
            orig_idx: obj_idx_to_new_index_map[id(image)] for orig_idx, image in enumerate(processed_images)
        }

        flattened_patches = processed_images
        width = [width[orig_idx_to_new_idx_map[orig_idx]] for orig_idx in orig_idx_to_new_idx_map]
        height = [height[orig_idx_to_new_idx_map[orig_idx]] for orig_idx in orig_idx_to_new_idx_map]
        rows = [rows[orig_idx_to_new_idx_map[orig_idx]] for orig_idx in orig_idx_to_new_idx_map]
        cols = [cols[orig_idx_to_new_idx_map[orig_idx]] for orig_idx in orig_idx_to_new_idx_map]

        encoded_outputs = BatchFeature(
            data={
                "flattened_patches": flattened_patches,
                "attention_mask": attention_masks,
                "width": width,
                "height": height,
                "rows": rows,
                "cols": cols,
            },
            tensor_type=return_tensors,
        )

        return encoded_outputs