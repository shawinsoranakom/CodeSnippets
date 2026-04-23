def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        last_hidden_state: torch.LongTensor | None = None,
        attention_mask: torch.BoolTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        position_ids: torch.LongTensor | None = None,
        labels: torch.LongTensor | None = None,
        **kwargs,
    ) -> tuple | BaseModelOutputWithPast:
        """
        Args:
            input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
                Indices of input sequence tokens. The first element of the sequence must the text token associated to the audio codebooks.
                The rest of the elements must be flatten audio codebooks.
            last_hidden_state (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`):
                Sequence of hidden-states at the output of the last layer of the main decoder. Used to contextualize `input_ids`
            attention_mask (`torch.Tensor` of shape `(batch_size, sequence_length)`, *optional*):
                Mask to avoid performing attention on padding token indices. Mask values selected in `[0, 1]`:

                - 1 for tokens that are **not masked**,
                - 0 for tokens that are **masked**.

                [What are attention masks?](../glossary#attention-mask)

                Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
                [`PreTrainedTokenizer.__call__`] for details.

                If `past_key_values` is used, optionally only the last `input_ids` have to be input (see
                `past_key_values`).

                If you want to change padding behavior, you should read [`modeling_opt._prepare_decoder_attention_mask`]
                and modify to your needs. See diagram 1 in [the paper](https://huggingface.co/papers/1910.13461) for more
                information on the default strategy.

                - 1 indicates the head is **not masked**,
                - 0 indicates the head is **masked**.
            past_key_values (`Cache`, *optional*):
                It is a [`~cache_utils.Cache`] instance. For more details, see our [kv cache guide](https://huggingface.co/docs/transformers/en/kv_cache).

                If `past_key_values` are used, the user can optionally input only the last `input_ids` (those that don't
                have their past key value states given to this model) of shape `(batch_size, 1)` instead of all `input_ids`
                of shape `(batch_size, sequence_length)`.
            inputs_embeds (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`, *optional*):
                Optionally, instead of passing `input_ids` you can choose to directly pass an embedded representation. This
                is useful if you want more control over how to convert the inputs into associated vectors than the
                model's internal embedding lookup matrix.
            use_cache (`bool`, *optional*):
                If set to `True`, `past_key_values` key value states are returned and can be used to speed up decoding (see
                `past_key_values`).
            output_attentions (`bool`, *optional*):
                Whether or not to return the attentions tensors of all attention layers. See `attentions` under returned
                tensors for more detail.
            output_hidden_states (`bool`, *optional*):
                Whether or not to return the hidden states of all layers. See `hidden_states` under returned tensors for
                more detail.
            return_dict (`bool`, *optional*):
                Whether or not to return a [`~utils.ModelOutput`] instead of a plain tuple.
            position_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
                Indices of positions of each input sequence tokens in the position embeddings. Selected in the range `[0,
                config.n_positions - 1]`.

                [What are position IDs?](../glossary#position-ids)
            labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
                Labels for computing the masked language modeling loss. Indices should either be in `[0, ...,
                config.vocab_size]` or -100 (see `input_ids` docstring). Tokens with indices set to `-100` are ignored
                (masked), the loss is only computed for the tokens with labels in `[0, ..., config.vocab_size]`.
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        use_cache = use_cache if use_cache is not None else self.config.use_cache

        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if self.gradient_checkpointing and self.training and use_cache:
            logger.warning_once(
                "`use_cache=True` is incompatible with gradient checkpointing. Setting `use_cache=False`."
            )
            use_cache = False

        if use_cache and past_key_values is None:
            past_key_values = DynamicCache(config=self.config)

        past_seen_tokens = 0 if past_key_values is None else past_key_values.get_seq_length()
        codebook_idx = torch.arange(input_ids.shape[1], device=input_ids.device) + past_seen_tokens

        if position_ids is None:
            position_ids = codebook_idx.unsqueeze(0)

        # If inputs_embeds is provided, it has the priority over input_ids, which won't be used
        if inputs_embeds is None:
            inputs_embeds = []
            for position_idx in codebook_idx:
                position_idx = position_idx.item()
                if position_idx == 0:
                    inputs_embeds.append(self.text_embed_tokens(input_ids[:, [position_idx]]))
                else:
                    inputs_embeds.append(
                        self.embed_tokens[(position_idx - 1)](input_ids[:, [position_idx - past_seen_tokens]])
                    )

            inputs_embeds = torch.cat(inputs_embeds, dim=1)

        inputs_embeds += self.input_projections(last_hidden_state, codebook_idx)

        causal_mask = None
        if attention_mask is not None:
            causal_mask = create_causal_mask(
                config=self.config,
                inputs_embeds=inputs_embeds,
                attention_mask=attention_mask,
                past_key_values=past_key_values,
                position_ids=position_ids,
            )

        # decoder layers
        all_hidden_states = () if output_hidden_states else None
        all_self_attns = () if output_attentions else None
        hidden_states = inputs_embeds
        for decoder_layer in self.layers:
            if output_hidden_states:
                all_hidden_states += (hidden_states,)

            layer_outputs = decoder_layer(
                hidden_states,
                attention_mask=causal_mask,
                position_ids=position_ids,
                past_key_values=past_key_values,
                output_attentions=output_attentions,
                use_cache=use_cache,
                codebook_idx=codebook_idx,
            )

            hidden_states = layer_outputs[0]

            if output_attentions:
                all_self_attns += (layer_outputs[1],)

        # add hidden states from the last decoder layer
        if output_hidden_states:
            all_hidden_states += (hidden_states,)

        logits = self.lm_heads(hidden_states, codebook_idx)

        loss = None
        if labels is not None:
            # Upcast to float if we need to compute the loss to avoid potential precision issues
            logits = logits.float()
            loss_fct = CrossEntropyLoss()

            labels = labels.masked_fill(labels == self.config.audio_vocab_size, -100).reshape(-1)
            labels = labels.to(logits.device)
            loss = loss_fct(logits.reshape(-1, self.config.audio_vocab_size), labels)

        if not return_dict:
            return tuple(
                v for v in [loss, logits, past_key_values, all_hidden_states, all_self_attns] if v is not None
            )

        return CausalLMOutputWithPast(
            loss=loss,
            logits=logits,
            past_key_values=past_key_values,
            hidden_states=past_key_values,
            attentions=all_self_attns,
        )