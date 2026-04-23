def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | BaseModelOutputWithPooling:
        r"""
        hidden_states (`torch.FloatTensor` of shape `(batch_size, image_num_patches + text_seq_len, hidden_size)`):
            The concatenated hidden states of unimodal encoders.
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        batch_size, seq_length, _ = hidden_states.size()

        if self.use_cls_token:
            cls_tokens = self.cls_token.expand(batch_size, -1, -1)
            hidden_states = torch.cat((cls_tokens, hidden_states), dim=1)
            seq_length += 1

        if attention_mask is None:
            attention_mask = torch.ones((batch_size, seq_length), device=hidden_states.device)

        extended_attention_mask: torch.Tensor = self.get_extended_attention_mask(
            attention_mask,
            (batch_size, seq_length),
        )

        encoder_outputs = self.encoder(
            hidden_states,
            attention_mask=extended_attention_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        sequence_output = encoder_outputs[0]
        sequence_output = self.layernorm(sequence_output)
        pooled_output = self.pooler(sequence_output) if self.pooler is not None else None

        if not return_dict:
            return (sequence_output, pooled_output) + encoder_outputs[1:]

        return BaseModelOutputWithPooling(
            last_hidden_state=sequence_output,
            pooler_output=pooled_output,
            hidden_states=encoder_outputs.hidden_states,
            attentions=encoder_outputs.attentions,
        )