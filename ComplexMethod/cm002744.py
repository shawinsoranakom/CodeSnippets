def forward(
        self,
        hidden_states: torch.Tensor,
        bool_masked_pos: torch.BoolTensor | None = None,
        output_attentions: bool = False,
        output_hidden_states: bool = False,
        return_dict: bool = True,
    ) -> tuple | BaseModelOutput:
        all_hidden_states = () if output_hidden_states else None
        all_reshaped_hidden_states = () if output_hidden_states else None
        all_self_attentions = () if output_attentions else None

        if output_hidden_states:
            all_hidden_states = all_hidden_states + (hidden_states,)
            reshaped_hidden_states = self.reroll(hidden_states, stage_idx=0, bool_masked_pos=bool_masked_pos)
            all_reshaped_hidden_states = all_reshaped_hidden_states + (reshaped_hidden_states,)

        for i, stage_module in enumerate(self.stages):
            layer_outputs = stage_module(hidden_states, output_attentions)

            hidden_states = layer_outputs[0]

            if output_attentions:
                all_self_attentions = all_self_attentions + (layer_outputs[1],)

            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states,)
                reshaped_hidden_states = self.reroll(hidden_states, stage_idx=i, bool_masked_pos=bool_masked_pos)
                all_reshaped_hidden_states = all_reshaped_hidden_states + (reshaped_hidden_states,)

        if not return_dict:
            return tuple(
                v
                for v in [hidden_states, all_hidden_states, all_self_attentions, all_reshaped_hidden_states]
                if v is not None
            )
        return HieraEncoderOutput(
            last_hidden_state=hidden_states,
            hidden_states=all_hidden_states,
            attentions=all_self_attentions,
            reshaped_hidden_states=all_reshaped_hidden_states,
        )