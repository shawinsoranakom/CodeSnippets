def forward(
        self,
        hidden_states: torch.Tensor,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
        interpolate_pos_encoding: bool = False,
        resolution: tuple[int, int] | None = None,
        return_dict: bool = True,
    ) -> tuple | BaseModelOutput:
        all_hidden_states = () if output_hidden_states else None
        all_self_attentions = () if output_attentions else None

        for i, layer_module in enumerate(self.layer):
            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states,)

            if self.has_relative_position_bias:
                height, width = resolution
                window_size = (height // self.config.patch_size, width // self.config.patch_size)
                relative_position_bias = self.relative_position_bias(
                    window_size, interpolate_pos_encoding=interpolate_pos_encoding, dim_size=hidden_states.shape[1]
                )
            else:
                relative_position_bias = None

            layer_outputs = layer_module(
                hidden_states,
                output_attentions=output_attentions,
                relative_position_bias=relative_position_bias,
                interpolate_pos_encoding=interpolate_pos_encoding,
                resolution=resolution,
            )

            hidden_states = layer_outputs[0]

            if output_attentions:
                all_self_attentions = all_self_attentions + (layer_outputs[1],)

        if output_hidden_states:
            all_hidden_states = all_hidden_states + (hidden_states,)

        if not return_dict:
            return tuple(v for v in [hidden_states, all_hidden_states, all_self_attentions] if v is not None)
        return BaseModelOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            attentions=all_self_attentions,
        )