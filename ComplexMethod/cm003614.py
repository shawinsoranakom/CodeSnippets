def get_image_features(
        self,
        pixel_values: torch.FloatTensor,
        image_sizes: torch.Tensor,
        vision_feature_layer: int | list[int] | list[int] | None = None,
        vision_feature_select_strategy: str | None = None,
        vision_aspect_ratio: str | None = None,
        batch_num_images: torch.LongTensor | None = None,
        output_hidden_states: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | BaseModelOutputWithPooling:
        r"""
        image_sizes (`torch.Tensor` of shape `(num_images, 2)`):
            Actual image size of each images (H, W).
        vision_aspect_ratio (`str`, *optional*, defaults to `"anyres_max_9"`):
            Aspect ratio used when processing image features. The default value is "anyres_max_9".
        batch_num_images (`torch.LongTensor`, *optional*):
            Number of images in each sample.
        """
        # ! infer image_num_patches from image_sizes
        if batch_num_images is None:
            # treat this as a single-image case for backward compatibility
            need_patching = [True] * len(image_sizes)
        else:
            need_patching = [n == 1 for n in batch_num_images for _ in range(n)]
        image_num_patches = [
            image_size_to_num_patches(
                image_size=imsize,
                grid_pinpoints=self.config.image_grid_pinpoints,
                patch_size=self.config.vision_config.image_size,
            )
            if should_patch
            else 1
            for imsize, should_patch in zip(image_sizes, need_patching)
        ]
        if pixel_values.dim() == 5:
            # stacked if input is (batch_size, num_patches, num_channels, height, width)
            _pixel_values_list = [pix_val[:num_patch] for pix_val, num_patch in zip(pixel_values, image_num_patches)]
            pixel_values = torch.cat(_pixel_values_list, dim=0)
        elif pixel_values.dim() != 4:
            # otherwise has to be stacked from list of (num_patches, num_channels, height, width)
            raise ValueError(f"pixel_values of shape {pixel_values.shape}, expect to be of 4 or 5 dimensions")

        image_outputs = self.vision_tower(
            pixel_values,
            output_hidden_states=True,  # Ignore arg on purpose
            return_dict=True,
            **kwargs,
        )
        # If we have one vision feature layer, return the corresponding hidden states,
        # otherwise, select the hidden states of each feature layer and concatenate them
        if isinstance(vision_feature_layer, int):
            selected_image_feature = image_outputs.hidden_states[vision_feature_layer]
        else:
            hs_pool = [image_outputs.hidden_states[layer_idx] for layer_idx in vision_feature_layer]
            selected_image_feature = torch.cat(hs_pool, dim=-1)

        if vision_feature_select_strategy == "default":
            selected_image_feature = selected_image_feature[:, 1:]
        image_features = self.multi_modal_projector(selected_image_feature)
        image_features = torch.split(image_features, image_num_patches, dim=0)

        image_features, feature_lens = self.pack_image_features(
            image_features,
            image_sizes,
            image_newline=self.image_newline,
            vision_aspect_ratio=vision_aspect_ratio,
        )
        image_outputs.pooler_output = image_features

        return image_outputs