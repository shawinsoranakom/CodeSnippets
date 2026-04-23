def forward(
        self,
        hidden_states: paddle.Tensor,
        input_dimensions: Tuple[int, int],
        head_mask=None,
        output_attentions=False,
        output_hidden_states=False,
        output_hidden_states_before_downsampling=False,
        always_partition=False,
        return_dict=True,
    ):
        all_hidden_states = () if output_hidden_states else None
        all_reshaped_hidden_states = () if output_hidden_states else None
        all_self_attentions = () if output_attentions else None

        if output_hidden_states:
            batch_size, _, hidden_size = hidden_states.shape
            reshaped_hidden_state = hidden_states.view(
                batch_size, *input_dimensions, hidden_size
            )
            reshaped_hidden_state = reshaped_hidden_state.permute(0, 3, 1, 2)
            all_hidden_states += (hidden_states,)
            all_reshaped_hidden_states += (reshaped_hidden_state,)

        for i, layer_module in enumerate(self.layers):
            layer_head_mask = head_mask[i] if head_mask is not None else None

            if self.gradient_checkpointing and self.training:
                layer_outputs = self._gradient_checkpointing_func(
                    layer_module.__call__,
                    hidden_states,
                    input_dimensions,
                    layer_head_mask,
                    output_attentions,
                    always_partition,
                )
            else:
                layer_outputs = layer_module(
                    hidden_states,
                    input_dimensions,
                    layer_head_mask,
                    output_attentions,
                    always_partition,
                )

            hidden_states = layer_outputs[0]

            hidden_states_before_downsampling = layer_outputs[1]
            output_dimensions = layer_outputs[2]

            input_dimensions = (output_dimensions[-2], output_dimensions[-1])

            if output_hidden_states and output_hidden_states_before_downsampling:
                batch_size, _, hidden_size = hidden_states_before_downsampling.shape
                reshaped_hidden_state = hidden_states_before_downsampling.reshape(
                    [
                        batch_size,
                        *(output_dimensions[0], output_dimensions[1]),
                        hidden_size,
                    ]
                )
                reshaped_hidden_state = reshaped_hidden_state.transpose([0, 3, 1, 2])
                all_hidden_states += (hidden_states_before_downsampling,)
                all_reshaped_hidden_states += (reshaped_hidden_state,)
            elif output_hidden_states and not output_hidden_states_before_downsampling:
                batch_size, _, hidden_size = hidden_states.shape
                reshaped_hidden_state = hidden_states.reshape(
                    [batch_size, *input_dimensions, hidden_size]
                )
                reshaped_hidden_state = reshaped_hidden_state.transpose([0, 3, 1, 2])
                all_hidden_states += (hidden_states,)
                all_reshaped_hidden_states += (reshaped_hidden_state,)

            if output_attentions:
                all_self_attentions += layer_outputs[3:]

        if not return_dict:
            return tuple(
                v
                for v in [hidden_states, all_hidden_states, all_self_attentions]
                if v is not None
            )

        return DonutSwinEncoderOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            attentions=all_self_attentions,
            reshaped_hidden_states=all_reshaped_hidden_states,
        )