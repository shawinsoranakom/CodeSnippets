def forward(
        self,
        hidden_states,
        attention_mask=None,
        padding_len=0,
        output_attentions=False,
        output_hidden_states=False,
        return_dict=True,
    ):
        is_index_masked = attention_mask < 0
        is_index_global_attn = attention_mask > 0

        # Record `is_global_attn == True` to enable ONNX export
        is_global_attn = is_index_global_attn.flatten().any().item()

        all_hidden_states = () if output_hidden_states else None
        all_attentions = () if output_attentions else None  # All local attentions.
        all_global_attentions = () if (output_attentions and is_global_attn) else None

        for idx, layer_module in enumerate(self.layer):
            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states,)

            layer_outputs = layer_module(
                hidden_states,
                attention_mask=attention_mask,
                is_index_masked=is_index_masked,
                is_index_global_attn=is_index_global_attn,
                is_global_attn=is_global_attn,
                output_attentions=output_attentions,
            )
            hidden_states = layer_outputs[0]

            if output_attentions:
                # bzs x seq_len x num_attn_heads x (num_global_attn + attention_window_len + 1) => bzs x num_attn_heads x seq_len x (num_global_attn + attention_window_len + 1)
                all_attentions = all_attentions + (layer_outputs[1].transpose(1, 2),)

                if is_global_attn:
                    # bzs x num_attn_heads x num_global_attn x seq_len => bzs x num_attn_heads x seq_len x num_global_attn
                    all_global_attentions = all_global_attentions + (layer_outputs[2].transpose(2, 3),)

        # Add last layer
        if output_hidden_states:
            all_hidden_states = all_hidden_states + (hidden_states,)

        # undo padding if necessary
        # unpad `hidden_states` because the calling function is expecting a length == input_ids.size(1)
        hidden_states = hidden_states[:, : hidden_states.shape[1] - padding_len]
        if output_hidden_states:
            all_hidden_states = tuple(state[:, : state.shape[1] - padding_len] for state in all_hidden_states)

        if output_attentions:
            all_attentions = tuple(state[:, :, : state.shape[2] - padding_len, :] for state in all_attentions)

        if not return_dict:
            return tuple(
                v for v in [hidden_states, all_hidden_states, all_attentions, all_global_attentions] if v is not None
            )
        return LongformerBaseModelOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            attentions=all_attentions,
            global_attentions=all_global_attentions,
        )