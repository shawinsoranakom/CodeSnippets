def forward(
        self,
        hidden_states: torch.Tensor,
        output_attentions: bool | None = False,
        output_hidden_states: bool | None = False,
        output_hidden_states_before_downsampling: bool | None = False,
        return_dict: bool | None = True,
    ) -> tuple | DinatEncoderOutput:
        all_hidden_states = () if output_hidden_states else None
        all_reshaped_hidden_states = () if output_hidden_states else None
        all_self_attentions = () if output_attentions else None

        if output_hidden_states:
            # rearrange b h w c -> b c h w
            reshaped_hidden_state = hidden_states.permute(0, 3, 1, 2)
            all_hidden_states += (hidden_states,)
            all_reshaped_hidden_states += (reshaped_hidden_state,)

        for i, layer_module in enumerate(self.levels):
            layer_outputs = layer_module(hidden_states, output_attentions)

            hidden_states = layer_outputs[0]
            hidden_states_before_downsampling = layer_outputs[1]

            if output_hidden_states and output_hidden_states_before_downsampling:
                # rearrange b h w c -> b c h w
                reshaped_hidden_state = hidden_states_before_downsampling.permute(0, 3, 1, 2)
                all_hidden_states += (hidden_states_before_downsampling,)
                all_reshaped_hidden_states += (reshaped_hidden_state,)
            elif output_hidden_states and not output_hidden_states_before_downsampling:
                # rearrange b h w c -> b c h w
                reshaped_hidden_state = hidden_states.permute(0, 3, 1, 2)
                all_hidden_states += (hidden_states,)
                all_reshaped_hidden_states += (reshaped_hidden_state,)

            if output_attentions:
                all_self_attentions += layer_outputs[2:]

        if not return_dict:
            return tuple(v for v in [hidden_states, all_hidden_states, all_self_attentions] if v is not None)

        return DinatEncoderOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            attentions=all_self_attentions,
            reshaped_hidden_states=all_reshaped_hidden_states,
        )