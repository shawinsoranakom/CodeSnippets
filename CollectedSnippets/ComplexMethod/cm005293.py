def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: torch.FloatTensor | None = None,
        inputs: torch.FloatTensor | None = None,
        inputs_mask: torch.FloatTensor | None = None,
        output_attentions: bool | None = False,
        output_hidden_states: bool | None = False,
        return_dict: bool | None = True,
    ) -> tuple | BaseModelOutputWithCrossAttentions:
        all_hidden_states = () if output_hidden_states else None
        all_self_attentions = () if output_attentions else None
        all_cross_attentions = () if output_attentions else None

        # Apply the cross-attention between the latents (hidden_states) and inputs:
        layer_outputs = self.cross_attention(
            hidden_states,
            attention_mask=attention_mask,
            inputs=inputs,
            inputs_mask=inputs_mask,
            output_attentions=output_attentions,
        )
        hidden_states = layer_outputs[0]

        if output_attentions:
            all_cross_attentions = all_cross_attentions + (layer_outputs[1],)

        # Apply the block of self-attention layers more than once:
        for _ in range(self.config.num_blocks):
            for i, layer_module in enumerate(self.self_attends):
                if output_hidden_states:
                    all_hidden_states = all_hidden_states + (hidden_states,)

                layer_outputs = layer_module(
                    hidden_states,
                    attention_mask=attention_mask,
                    output_attentions=output_attentions,
                )

                hidden_states = layer_outputs[0]
                if output_attentions:
                    all_self_attentions = all_self_attentions + (layer_outputs[1],)

            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states,)

        if not return_dict:
            return tuple(
                v
                for v in [hidden_states, all_hidden_states, all_self_attentions, all_cross_attentions]
                if v is not None
            )
        return BaseModelOutputWithCrossAttentions(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            attentions=all_self_attentions,
            cross_attentions=all_cross_attentions,
        )