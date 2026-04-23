def forward(
            self,
            hidden_states: torch.Tensor,
            attention_mask: Optional[torch.Tensor] = None,
            head_mask: Optional[torch.Tensor] = None,
            output_attentions: bool = False,
            output_hidden_states: bool = False,
            return_dict: bool = False,
            **kwargs,
        ):
            position_bias = self.compute_position_bias(hidden_states)
            all_hidden_states = () if output_hidden_states else None
            all_attentions = () if output_attentions else None

            for i, layer_module in enumerate(self.layer):
                if output_hidden_states:
                    all_hidden_states = all_hidden_states + (hidden_states,)

                # do gradient checkpointing if enabled and training
                if getattr(self, "gradient_checkpointing", False) and self.training:

                    def create_custom_forward(module):
                        # bog standard checkpoint
                        def custom_forward(*inputs):
                            return module(*inputs, output_attentions = output_attentions)

                        return custom_forward

                    layer_outputs = torch.utils.checkpoint.checkpoint(
                        create_custom_forward(layer_module),
                        hidden_states,
                        attention_mask,
                        head_mask[i] if head_mask is not None else None,
                        position_bias,
                        use_reentrant = True,  # fix for torch 2.9
                    )
                else:
                    # original code from here on
                    layer_outputs = layer_module(
                        hidden_states,
                        attention_mask,
                        head_mask[i] if head_mask is not None else None,
                        position_bias,
                        output_attentions = output_attentions,
                        **kwargs,
                    )

                hidden_states = layer_outputs[0]

                if output_attentions:
                    all_attentions = all_attentions + (layer_outputs[1],)

            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states,)

            if not return_dict:
                return tuple(
                    v
                    for v in [hidden_states, all_hidden_states, all_attentions]
                    if v is not None
                )
            return BaseModelOutput(
                last_hidden_state = hidden_states,
                hidden_states = all_hidden_states,
                attentions = all_attentions,
            )