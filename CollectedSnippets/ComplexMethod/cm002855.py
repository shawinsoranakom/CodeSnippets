def forward(
        self,
        pixel_values: torch.Tensor,
        **kwargs: Unpack[TransformersKwargs],
    ) -> DINOv3ViTBackboneOutput:
        pixel_values = pixel_values.to(self.embeddings.patch_embeddings.weight.dtype)
        hidden_states = self.embeddings(pixel_values)
        position_embeddings = self.rope_embeddings(pixel_values)

        kwargs["output_hidden_states"] = True  # required to extract layers for the stages
        output = self.model(hidden_states, position_embeddings, **kwargs)
        stage_hidden_states = output.hidden_states

        batch_size, _, image_height, image_width = pixel_values.shape
        patch_size = self.config.patch_size
        num_patches_height = image_height // patch_size
        num_patches_width = image_width // patch_size

        num_prefix = 1 + getattr(self.config, "num_register_tokens", 0)
        return_class_token = getattr(self.config, "return_class_token", False)

        feature_maps, cls_tokens = [], []
        sequence_output = None
        last_stage_idx = len(self.stage_names) - 1
        for idx, (stage_name, hidden_state) in enumerate(zip(self.stage_names, stage_hidden_states)):
            if idx == last_stage_idx:
                hidden_state = self.norm(hidden_state)
                sequence_output = hidden_state
            elif self.config.apply_layernorm:
                hidden_state = self.norm(hidden_state)

            if stage_name in self.out_features:
                if return_class_token:
                    cls_tokens.append(hidden_state[:, 0, :])
                patch_tokens = hidden_state[:, num_prefix:, :]
                if self.config.reshape_hidden_states:
                    fmap = (
                        patch_tokens.reshape(batch_size, num_patches_height, num_patches_width, patch_tokens.shape[-1])
                        .permute(0, 3, 1, 2)
                        .contiguous()
                    )
                else:
                    fmap = patch_tokens

                feature_maps.append(fmap)

        output = DINOv3ViTBackboneOutput(
            feature_maps=tuple(feature_maps),
            cls_tokens=tuple(cls_tokens) if return_class_token else None,
            hidden_states=output.hidden_states,
            attentions=output.attentions,
        )
        output.last_hidden_state = sequence_output

        return output