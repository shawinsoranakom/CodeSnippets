def forward(
        self,
        pixel_values: Tensor,
        output_hidden_states: bool | None = None,
        output_attentions: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> BackboneOutput:
        return_dict = return_dict if return_dict is not None else self.config.return_dict
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions

        outputs = self.model(
            pixel_values, output_hidden_states=True, output_attentions=output_attentions, return_dict=True
        )

        # we skip the stem
        hidden_states = outputs.hidden_states[1:]

        # we need to reshape the hidden states to their original spatial dimensions
        # spatial dimensions contains all the heights and widths of each stage, including after the embeddings
        spatial_dimensions: tuple[tuple[int, int]] = outputs.hidden_states_spatial_dimensions
        feature_maps = ()
        for i, (hidden_state, stage, (height, width)) in enumerate(
            zip(hidden_states, self.stage_names[1:], spatial_dimensions)
        ):
            norm = self.hidden_states_norms[i]
            # the last element correspond to the layer's last block output but before patch merging
            hidden_state_unpolled = hidden_state[-1]
            hidden_state_norm = norm(hidden_state_unpolled)
            # the pixel decoder (FPN) expects 3D tensors (features)
            batch_size, _, hidden_size = hidden_state_norm.shape
            # reshape "b (h w) d -> b d h w"
            hidden_state_permuted = (
                hidden_state_norm.permute(0, 2, 1).view((batch_size, hidden_size, height, width)).contiguous()
            )
            if stage in self.out_features:
                feature_maps += (hidden_state_permuted,)

        if not return_dict:
            output = (feature_maps,)
            if output_hidden_states:
                output += (outputs.hidden_states,)
            if output_attentions:
                output += (outputs.attentions,)
            return output

        return BackboneOutput(
            feature_maps=feature_maps,
            hidden_states=outputs.hidden_states if output_hidden_states else None,
            attentions=outputs.attentions,
        )