def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        encoder_hidden_states: torch.Tensor | None = None,
        encoder_attention_mask: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.Tensor | None = None,
        use_cache: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | ProphetNetDecoderModelOutput:
        r"""
        Example:

        ```python
        >>> from transformers import AutoTokenizer, ProphetNetDecoder
        >>> import torch

        >>> tokenizer = AutoTokenizer.from_pretrained("microsoft/prophetnet-large-uncased")
        >>> model = ProphetNetDecoder.from_pretrained("microsoft/prophetnet-large-uncased", add_cross_attention=False)
        >>> inputs = tokenizer("Hello, my dog is cute", return_tensors="pt")
        >>> outputs = model(**inputs)

        >>> last_hidden_states = outputs.last_hidden_state
        ```"""
        use_cache = use_cache if use_cache is not None else self.config.use_cache
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if input_ids is None and inputs_embeds is None:
            raise ValueError("Either `decoder_input_ids` or `decoder_inputs_embeds` has to be passed.")
        elif input_ids is not None and inputs_embeds is not None:
            raise ValueError("Make sure to only pass `decoder_input_ids` or `decoder_inputs_embeds`.")
        elif input_ids is not None and inputs_embeds is None:
            inputs_embeds = self.word_embeddings(input_ids)

        batch_size, sequence_length = inputs_embeds.shape[:2]

        if self.gradient_checkpointing and self.training:
            if use_cache:
                logger.warning_once(
                    "`use_cache=True` is incompatible with gradient checkpointing. Setting `use_cache=False`..."
                )
                use_cache = False

        if use_cache and past_key_values is None:
            past_key_values = (
                EncoderDecoderCache(DynamicCache(config=self.config), DynamicCache(config=self.config))
                if encoder_hidden_states is not None or self.config.is_encoder_decoder
                else DynamicCache(config=self.config)
            )

        past_key_values_length = past_key_values.get_seq_length() if past_key_values is not None else 0

        main_stream_pos_embed, position_ids = self.position_embeddings(
            (batch_size, sequence_length),
            device=inputs_embeds.device,
            past_key_values=past_key_values,
        )

        if past_key_values_length != 0:
            main_relative_position_buckets, predict_relative_position_buckets = None, None
        else:
            (
                main_relative_position_buckets,
                predict_relative_position_buckets,
            ) = self.compute_buffered_relative_buckets(position_ids)
        predicting_stream_pos_embed = self.position_embeddings._forward(position_ids + 1)

        # add position embeddings
        hidden_states = inputs_embeds + main_stream_pos_embed

        ngram_embeddings = self.ngram_embeddings.weight

        # prepare attention mask
        if past_key_values_length != 0:
            assert hidden_states.size(1) == 1, (
                "At the moment `use_cache` is only supported for `decoder_input_ids` of length 1"
            )

            ngram_hidden_states = [
                (ngram_embeddings[ngram - 1] + predicting_stream_pos_embed).repeat(batch_size, 1, 1)
                for ngram in range(self.ngram)
            ]
            extended_attention_mask = None
            extended_predict_attention_mask = None
        else:
            ngram_hidden_states = [
                (ngram_embeddings[ngram - 1] + predicting_stream_pos_embed) for ngram in range(self.ngram)
            ]
            extended_attention_mask = self.prepare_attention_mask(hidden_states, attention_mask)
            extended_predict_attention_mask = self.prepare_predict_attention_mask(hidden_states, attention_mask)

        # prepare encoder attention mask
        if encoder_attention_mask is not None:
            extended_encoder_attention_mask = (
                1.0 - encoder_attention_mask[:, None, None, :].repeat(1, self.config.num_decoder_attention_heads, 1, 1)
            ) * torch.finfo(self.dtype).min
            extended_encoder_attention_mask = extended_encoder_attention_mask.to(inputs_embeds.dtype)
        else:
            extended_encoder_attention_mask = None

        hidden_states = torch.cat([hidden_states] + ngram_hidden_states, 1)

        if self.embeddings_layer_norm:
            hidden_states = self.embeddings_layer_norm(hidden_states)

        hidden_states = nn.functional.dropout(hidden_states, p=self.dropout, training=self.training)

        # init attentions, hidden_states and cache with empty tuples
        all_main_stream_hidden_states = () if output_hidden_states else None
        all_ngram_stream_hidden_states = () if output_hidden_states and self.config.ngram > 0 else None

        all_main_stream_attns = () if output_attentions else None
        all_ngram_stream_attns = () if output_attentions else None
        all_cross_attns = () if output_attentions and self.config.add_cross_attention else None

        for idx, decoder_layer in enumerate(self.layers):
            if output_hidden_states:
                # grad cannot be kept because tensor is sliced
                all_main_stream_hidden_states += (hidden_states[:, :sequence_length],)
                if self.config.ngram > 0:
                    all_ngram_stream_hidden_states += (hidden_states[:, sequence_length:],)

            layer_outputs = decoder_layer(
                hidden_states,
                extended_attention_mask,
                encoder_hidden_states,  # as a positional argument for gradient checkpointing
                encoder_attn_mask=extended_encoder_attention_mask,
                extended_predict_attention_mask=extended_predict_attention_mask,
                main_relative_position_buckets=main_relative_position_buckets,
                predict_relative_position_buckets=predict_relative_position_buckets,
                position_ids=position_ids,
                past_key_values=past_key_values,
                use_cache=use_cache,
                output_attentions=output_attentions,
            )

            hidden_states = layer_outputs[0]
            if output_attentions:
                all_main_stream_attns += (layer_outputs[1],)
                all_ngram_stream_attns += (layer_outputs[2],)

                if self.config.add_cross_attention:
                    all_cross_attns += (layer_outputs[3],)

        if output_hidden_states:
            all_main_stream_hidden_states += (hidden_states[:, :sequence_length],)
            if self.config.ngram > 0:
                all_ngram_stream_hidden_states += (hidden_states[:, sequence_length:],)

        # split last_hidden_state for return
        last_hidden_state = hidden_states[:, :sequence_length]
        last_hidden_state_ngram = hidden_states[:, sequence_length:] if self.config.ngram > 0 else None

        if not return_dict:
            return tuple(
                v
                for v in [
                    last_hidden_state,
                    last_hidden_state_ngram,
                    past_key_values,
                    all_main_stream_hidden_states,
                    all_ngram_stream_hidden_states,
                    all_main_stream_attns,
                    all_ngram_stream_attns,
                    all_cross_attns,
                ]
                if v is not None
            )
        return ProphetNetDecoderModelOutput(
            last_hidden_state=last_hidden_state,
            last_hidden_state_ngram=last_hidden_state_ngram,
            past_key_values=past_key_values,
            hidden_states=all_main_stream_hidden_states,
            hidden_states_ngram=all_ngram_stream_hidden_states,
            attentions=all_main_stream_attns,
            ngram_attentions=all_ngram_stream_attns,
            cross_attentions=all_cross_attns,
        )