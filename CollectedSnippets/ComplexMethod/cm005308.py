def get_image_features(
        self,
        pixel_values: torch.FloatTensor,
        vision_feature_layer: int | list[int] | list[int] | None = None,
        vision_feature_select_strategy: str | None = None,
        output_hidden_states: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | BaseModelOutputWithPooling:
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        # this is not memory efficient at all (output_hidden_states=True) will save all the hidden states.
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
            if vision_feature_select_strategy == "default":
                selected_image_feature = selected_image_feature[:, 1:]
        else:
            hs_pool = [image_outputs.hidden_states[layer_idx] for layer_idx in vision_feature_layer]
            # For default; crop CLS from each hidden state in the hidden state pool
            if vision_feature_select_strategy == "default":
                hs_pool = [hs[:, 1:] for hs in hs_pool]
            selected_image_feature = torch.cat(hs_pool, dim=-1)

        image_features = self.multi_modal_projector(selected_image_feature)

        # If image_sizes is provided, we need to split the image features accordingly,
        # but only if the image_sizes is not None (the default in this and related architectures)
        if kwargs.get("image_sizes") is not None:
            split_sizes = (
                (torch.as_tensor(kwargs["image_sizes"], device=image_features.device) // self.vision_tower.patch_size)
                .prod(dim=-1)
                .tolist()
            )
            image_features = torch.split(image_features.squeeze(0), split_sizes)
        else:
            image_features = list(image_features)
        image_outputs.pooler_output = image_features

        return image_outputs