def forward(
        self,
        input_ids: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        past_key_values: Cache | None = None,
        use_cache: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor] | BaseModelOutputWithPast:
        r"""
        input_ids (`torch.Tensor` of shape `(batch_size, seq_len)`):
            Indices of input sequence tokens in the vocabulary.

            Indices can be obtained using [`CPMAntTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            [What are input IDs?](../glossary#input-ids)
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict
        use_cache = use_cache if use_cache is not None else self.config.use_cache

        # add prompts ahead
        if input_ids.dtype != torch.int32:
            input_ids = input_ids.to(torch.int32)
        dtype, device = input_ids.dtype, input_ids.device
        segment = torch.where(input_ids != 0, 2, 0).to(dtype=dtype, device=device)
        length = (segment != 0).sum(-1).to(dtype=dtype, device=device)
        input_ids = torch.cat(
            (
                torch.arange(
                    self.prompt_length * 2 + self.vocab_size,
                    self.prompt_length * 3 + self.vocab_size,
                    dtype=dtype,
                    device=device,
                ).repeat(input_ids.size(0), 1),
                input_ids,
            ),
            dim=1,
        )
        batch, seq_length = input_ids.size()
        segment = torch.cat((torch.zeros(batch, self.prompt_length, dtype=dtype, device=device), segment), dim=1)
        context = torch.full((batch, seq_length), 1, dtype=dtype, device=device)
        position = torch.arange(seq_length, dtype=dtype, device=device).repeat(batch, 1)
        span = torch.full((batch, seq_length), 0, dtype=dtype, device=device)

        if use_cache and past_key_values is None:
            past_key_values = DynamicCache(config=self.config)

        past_length = past_key_values.get_seq_length() if past_key_values is not None else 0
        input_ids = input_ids.contiguous()
        hidden_states = self.input_embedding(input_ids)
        segment_states = self.segment_embedding(segment)
        if past_length != 0:
            segment_states = segment_states[:, -1:, :]

        hidden_states = hidden_states + segment_states

        attention_mask = self._prepare_attention_mask(input_ids, span, context, length)
        position_bias = self.position_bias(position, position, segment, segment)

        attention_mask = attention_mask[:, past_length:, :]
        position_bias = position_bias[:, :, past_length:, :]
        hidden_states = hidden_states[:, past_length:, :]

        hidden_states, all_hidden_states, all_attentions = self.encoder(
            hidden_states,
            attention_mask,
            position_bias,
            output_attentions,
            output_hidden_states,
            past_key_values,
            use_cache,
        )

        if past_length == 0:
            hidden_states = hidden_states[:, self.prompt_length :, :]
            # drop the prompt
            if all_attentions is not None:
                new_attentions = ()
                for attention in all_attentions:
                    new_attentions += (attention[:, :, self.prompt_length :, self.prompt_length :],)
                all_attentions = new_attentions
            if all_hidden_states is not None:
                new_hidden_states = ()
                for hidden_state in all_hidden_states:
                    new_hidden_states += (hidden_state[:, self.prompt_length :, :],)
                all_hidden_states = new_hidden_states

        if not return_dict:
            return tuple(
                v for v in [hidden_states, past_key_values, all_hidden_states, all_attentions] if v is not None
            )

        return BaseModelOutputWithPast(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values,
            hidden_states=all_hidden_states,
            attentions=all_attentions,
        )