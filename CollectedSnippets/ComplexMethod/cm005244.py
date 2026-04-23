def forward(
        self,
        input_ids: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.Tensor | None = None,
        labels: torch.LongTensor | None = None,
        inputs_embeds: torch.Tensor | None = None,
        use_cache: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor] | CausalLMOutputWithPast:
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        use_cache = use_cache if use_cache is not None else self.config.use_cache
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        loss = None
        if labels is not None:
            raise NotImplementedError(
                "Training is not implemented yet for Bark - ensure you do not pass `labels` to the model."
            )

        # Verify if inputs_embeds already exists
        # then compute embeddings.
        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both input_ids and inputs_embeds at the same time")
        elif inputs_embeds is not None and past_key_values is None:
            # we want to return the inputs_embeds in priority so that it is in line with a weird hack
            # of Bark which concatenate two bits of the inputs_embeds on the first forward pass of the semantic model
            pass
        elif input_ids is not None:
            inputs_embeds = self.input_embeds_layer(input_ids)  # token embeddings of shape (b, t, n_embd)
        elif inputs_embeds is not None:
            pass
        else:
            raise ValueError("You have to specify either input_ids or inputs_embeds")

        input_shape = inputs_embeds.size()[:-1]
        seq_length = input_shape[-1]

        if self.gradient_checkpointing and self.training:
            if use_cache:
                logger.warning_once(
                    "`use_cache=True` is incompatible with gradient checkpointing. Setting `use_cache=False`..."
                )
                use_cache = False

        if use_cache and past_key_values is None:
            past_key_values = DynamicCache(config=self.config)

        past_length = past_key_values.get_seq_length() if past_key_values is not None else 0
        inputs_embeds = inputs_embeds.to(self.position_embeds_layer.weight.device)

        if position_ids is None:
            position_ids = torch.arange(
                past_length,
                seq_length + past_length,
                dtype=torch.long,
                device=self.position_embeds_layer.weight.device,
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
                past_key_values=past_key_values,
                attention_mask=attention_mask,
                use_cache=use_cache,
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

        logits = self.lm_head(hidden_states)

        if not return_dict:
            return tuple(
                v for v in [None, logits, past_key_values, all_hidden_states, all_self_attentions] if v is not None
            )

        return CausalLMOutputWithPast(
            loss=loss,
            logits=logits,
            past_key_values=past_key_values,
            hidden_states=all_hidden_states,
            attentions=all_self_attentions,
        )