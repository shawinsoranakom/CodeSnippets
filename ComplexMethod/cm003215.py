def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.LongTensor | None = None,
        use_cache: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor, ...] | BaseModelOutputWithPastAndCrossAttentions:
        r"""
        input_ids (`torch.LongTensor` of shape `(batch_size, input_ids_length)`):
            `input_ids_length` = `sequence_length` if `past_key_values` is `None` else `past_key_values.get_seq_length()`
            (`sequence_length` of input past key value states). Indices of input sequence tokens in the vocabulary.

            If `past_key_values` is used, only `input_ids` that do not have their past calculated should be passed as
            `input_ids`.

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            [What are input IDs?](../glossary#input-ids)
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        use_cache = use_cache if use_cache is not None else self.config.use_cache
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if self.gradient_checkpointing and self.training:
            if use_cache:
                logger.warning_once(
                    "`use_cache=True` is incompatible with gradient checkpointing. Setting `use_cache=False`..."
                )
                use_cache = False

        if inputs_embeds is None:
            inputs_embeds = self.word_embeddings(input_ids)

        if use_cache and past_key_values is None:
            past_key_values = DynamicCache(config=self.config)

        # Compute alibi tensor: check build_alibi_tensor documentation
        alibi = None
        past_key_values_length = past_key_values.get_seq_length() if past_key_values is not None else 0
        batch_size, seq_length, _ = inputs_embeds.shape
        if self.use_alibi:
            mask = (
                torch.ones(
                    (batch_size, seq_length + past_key_values_length), device=inputs_embeds.device, dtype=torch.long
                )
                if attention_mask is None
                else attention_mask
            )
            alibi = build_alibi_tensor(mask, self.num_heads, dtype=inputs_embeds.dtype)

        if position_ids is None:
            past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0
            position_ids = torch.arange(inputs_embeds.shape[1], device=inputs_embeds.device) + past_seen_tokens
            position_ids = position_ids.unsqueeze(0)

        causal_mask = create_causal_mask(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
            # Force mask creation for alibi
            and_mask_function=lambda *args: torch.tensor(True, dtype=torch.bool),
        )
        if alibi is not None and causal_mask is not None and causal_mask.ndim == 4:
            min_dtype = torch.finfo(inputs_embeds.dtype).min

            # Only using non-bool mask for alibi
            if causal_mask.dtype == torch.bool:
                causal_mask = torch.where(
                    causal_mask, torch.tensor(0.0, device=causal_mask.device, dtype=inputs_embeds.dtype), min_dtype
                )

            # We take care to integrate alibi bias in the causal_mask here
            alibi = alibi.reshape(batch_size, -1, *alibi.shape[1:])
            causal_mask = torch.masked_fill(
                alibi / math.sqrt(self.config.hidden_size // self.num_heads),
                causal_mask < -1,
                min_dtype,
            )

        hidden_states = inputs_embeds
        position_embeddings = self.rotary_emb(hidden_states, position_ids=position_ids)

        all_self_attentions = () if output_attentions else None
        all_hidden_states = () if output_hidden_states else None

        for i, block in enumerate(self.h):
            if output_hidden_states:
                all_hidden_states = all_hidden_states + (hidden_states,)

            outputs = block(
                hidden_states,
                layer_past=past_key_values,
                attention_mask=causal_mask,
                position_ids=position_ids,
                use_cache=use_cache,
                output_attentions=output_attentions,
                alibi=alibi,
                position_embeddings=position_embeddings,
            )

            hidden_states = outputs[0]
            if output_attentions:
                all_self_attentions = all_self_attentions + (outputs[1],)

        # Add last hidden state
        hidden_states = self.ln_f(hidden_states)

        if output_hidden_states:
            all_hidden_states = all_hidden_states + (hidden_states,)

        if not return_dict:
            return tuple(
                v for v in [hidden_states, past_key_values, all_hidden_states, all_self_attentions] if v is not None
            )

        return BaseModelOutputWithPastAndCrossAttentions(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values,
            hidden_states=all_hidden_states,
            attentions=all_self_attentions,
        )