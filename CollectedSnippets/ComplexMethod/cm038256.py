def forward(
        self,
        input_ids: torch.Tensor | None,
        positions: torch.Tensor,
        intermediate_tensors: IntermediateTensors | None,
        inputs_embeds: torch.Tensor | None = None,
    ) -> torch.Tensor | IntermediateTensors:
        if get_pp_group().is_first_rank:
            if inputs_embeds is not None:
                hidden_states = inputs_embeds
            else:
                hidden_states = self.embed_input_ids(input_ids)
            residual = None
        else:
            assert intermediate_tensors is not None
            hidden_states = intermediate_tensors["hidden_states"]
            residual = intermediate_tensors["residual"]

        bskcn_h_1 = None
        bskcn_h_2 = None
        bskcn_r_1 = None
        bskcn_r_2 = None
        bskcn_tv = self.config.bskcn_tv[0] if self.training else self.config.bskcn_tv[1]

        for i in range(self.start_layer, self.end_layer):
            if i in self.config.bskcn_1:
                bskcn_h_1 = hidden_states.clone()
                bskcn_r_1 = residual.clone()
            if i in self.config.bskcn_2:
                bskcn_h_2 = hidden_states.clone()
                bskcn_r_2 = residual.clone()
            if i in self.config.bskcn_3:
                hidden_states = bskcn_h_1 * bskcn_tv + hidden_states * (1 - bskcn_tv)
                residual = bskcn_r_1 * bskcn_tv + residual * (1 - bskcn_tv)
            if i in self.config.bskcn_4:
                hidden_states = bskcn_h_2 * bskcn_tv + hidden_states * (1 - bskcn_tv)
                residual = bskcn_r_2 * bskcn_tv + residual * (1 - bskcn_tv)
            layer = self.layers[i]
            hidden_states, residual = layer(
                positions,
                hidden_states,
                residual,
            )

        if not get_pp_group().is_last_rank:
            return IntermediateTensors(
                {"hidden_states": hidden_states, "residual": residual}
            )

        hidden_states, _ = self.norm(hidden_states, residual)
        return hidden_states