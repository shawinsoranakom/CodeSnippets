def forward(
        self,
        codebook_idx: int,  # an additional idx corresponding to the id of the codebook that will be predicted
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        labels: torch.LongTensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor] | MaskedLMOutput:
        r"""
        codebook_idx (`int`):
            Index of the codebook that will be predicted.
        labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            NOT IMPLEMENTED YET.
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        loss = None
        if labels is not None:
            raise NotImplementedError("Training is not implemented yet")

        if codebook_idx == 0:
            raise ValueError("Cannot predict 0th codebook - 0th codebook should be predicted by the coarse model")

        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both input_ids and inputs_embeds at the same time")

        if input_ids is None and inputs_embeds is None:
            raise ValueError("You have to specify either input_ids or inputs_embeds")

        if input_ids is not None:
            # the input_embeddings are the sum of the j previous codebooks embeddings before
            # the current codebook_idx codebook

            # forward the GPT model itself
            inputs_embeds = [
                input_embeds_layer(input_ids[:, :, i]).unsqueeze(-1)
                for i, input_embeds_layer in enumerate(self.input_embeds_layers)
            ]  # token embeddings of shape (b, t, n_embd)
            inputs_embeds = torch.cat(inputs_embeds, dim=-1)
            inputs_embeds = inputs_embeds[:, :, :, : codebook_idx + 1].sum(dim=-1)

        input_shape = inputs_embeds.size()[:-1]
        seq_length = input_shape[1]

        inputs_embeds = inputs_embeds.to(self.position_embeds_layer.weight.device)

        if position_ids is None:
            position_ids = torch.arange(
                0, seq_length, dtype=torch.long, device=self.position_embeds_layer.weight.device
            )
            position_ids = position_ids.unsqueeze(0)  # shape (1, seq_length)

        position_ids = position_ids.to(self.position_embeds_layer.weight.device)
        position_embeds = self.position_embeds_layer(position_ids)  # position embeddings of shape (1, t, n_embd)

        attention_mask = create_bidirectional_mask(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
        )

        hidden_states = self.drop(inputs_embeds + position_embeds)
        output_shape = input_shape + (hidden_states.size(-1),)

        all_self_attentions = () if output_attentions else None
        all_hidden_states = () if output_hidden_states else None

        for i, block in enumerate(self.layers):
            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states,)

            outputs = block(
                hidden_states,
                attention_mask=attention_mask,
                output_attentions=output_attentions,
            )

            hidden_states = outputs[0]

            if output_attentions:
                all_self_attentions = all_self_attentions + (outputs[1],)

        hidden_states = self.layernorm_final(hidden_states)
        hidden_states = hidden_states.view(output_shape)

        # Add last hidden state
        if output_hidden_states:
            all_hidden_states = all_hidden_states + (hidden_states,)

        logits = self.lm_heads[codebook_idx - self.config.n_codes_given](hidden_states)

        if not return_dict:
            return tuple(v for v in [None, logits, all_hidden_states, all_self_attentions] if v is not None)

        return MaskedLMOutput(
            loss=loss,
            logits=logits,
            hidden_states=all_hidden_states,
            attentions=all_self_attentions,
        )