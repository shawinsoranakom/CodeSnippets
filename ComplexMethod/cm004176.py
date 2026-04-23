def forward(
        self,
        pixel_values: torch.FloatTensor,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> BackboneOutput | tuple[Tensor, ...]:
        return_dict = return_dict if return_dict is not None else self.config.return_dict
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions

        if output_attentions:
            raise ValueError("Cannot output attentions for timm backbones at the moment")

        if output_hidden_states:
            # We modify the return layers to include all the stages of the backbone
            self._backbone.return_layers = self._all_layers
            hidden_states = self._backbone(pixel_values, **kwargs)
            self._backbone.return_layers = self._return_layers
            feature_maps = tuple(hidden_states[i] for i in self.out_indices)
        else:
            feature_maps = self._backbone(pixel_values, **kwargs)
            hidden_states = None

        feature_maps = tuple(feature_maps)
        hidden_states = tuple(hidden_states) if hidden_states is not None else None

        if not return_dict:
            output = (feature_maps,)
            if output_hidden_states:
                output = output + (hidden_states,)
            return output

        return BackboneOutput(feature_maps=feature_maps, hidden_states=hidden_states, attentions=None)