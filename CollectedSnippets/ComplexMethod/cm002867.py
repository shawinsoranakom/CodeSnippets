def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        decoder_input_ids: torch.LongTensor | None = None,
        decoder_attention_mask: torch.Tensor | None = None,
        decoder_position_ids: torch.LongTensor | None = None,
        encoder_outputs: BaseModelOutput | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        decoder_inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> SequenceClassifierOutput:
        r"""
        decoder_position_ids (`torch.LongTensor` of shape `(batch_size, decoder_sequence_length)`, *optional*):
            Indices of positions of each decoder input sequence tokens in the position embeddings. Selected in the range `[0,
            config.decoder.n_positions - 1]`. [What are position IDs?](../glossary#position-ids)
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the sequence classification/regression loss. Indices should be in `[0, ...,
            config.num_labels - 1]`. If `config.num_labels == 1` a regression loss is computed (Mean-Square loss), If
            `config.num_labels > 1` a classification loss is computed (Cross-Entropy).
        """
        if self.config.is_encoder_decoder and (input_ids is None and inputs_embeds is not None):
            raise NotImplementedError(
                f"Passing input embeddings is currently not supported for {self.__class__.__name__} in encoder-decoder mode."
            )

        # Following T5, we automatically creates decoder_input_ids from input_ids if no decoder_input_ids are provided
        if self.config.is_encoder_decoder and (decoder_input_ids is None and decoder_inputs_embeds is None):
            if input_ids is None:
                raise ValueError(
                    "If no `decoder_input_ids` or `decoder_inputs_embeds` are "
                    "passed, `input_ids` cannot be `None`. Please pass either "
                    "`input_ids` or `decoder_input_ids` or `decoder_inputs_embeds`."
                )
            decoder_input_ids = self._shift_right(input_ids)

        if self.config.is_encoder_decoder:
            outputs: Seq2SeqModelOutput = self.model(
                input_ids,
                attention_mask=attention_mask,
                position_ids=position_ids,
                decoder_input_ids=decoder_input_ids,
                decoder_attention_mask=decoder_attention_mask,
                decoder_position_ids=decoder_position_ids,
                encoder_outputs=encoder_outputs,
                inputs_embeds=inputs_embeds,
                decoder_inputs_embeds=decoder_inputs_embeds,
                use_cache=False,
                **kwargs,
            )
            last_hidden_state = outputs.last_hidden_state
            hidden_states = outputs.decoder_hidden_states
            attentions = outputs.decoder_attentions
        else:
            outputs: BaseModelOutput = self.model(
                input_ids,
                attention_mask=attention_mask,
                position_ids=position_ids,
                inputs_embeds=inputs_embeds,
                **kwargs,
            )
            last_hidden_state = outputs.last_hidden_state
            hidden_states = outputs.hidden_states
            attentions = outputs.attentions

        logits = self.score(last_hidden_state)

        if input_ids is not None:
            batch_size = input_ids.shape[0]
        else:
            batch_size = inputs_embeds.shape[0]

        if self.config.pad_token_id is None and batch_size != 1:
            raise ValueError("Cannot handle batch sizes > 1 if no padding token is defined.")
        if self.config.pad_token_id is None:
            last_non_pad_token = -1
        elif input_ids is not None:
            # To handle both left- and right- padding, we take the rightmost token that is not equal to pad_token_id
            non_pad_mask = (input_ids != self.config.pad_token_id).to(logits.device, torch.int32)
            token_indices = torch.arange(input_ids.shape[-1], device=logits.device, dtype=torch.int32)
            last_non_pad_token = (token_indices * non_pad_mask).argmax(-1)

            if self.config.is_encoder_decoder:
                last_non_pad_token += 1  # due to the right shift.
                last_non_pad_token = torch.clamp(last_non_pad_token, max=decoder_input_ids.shape[-1] - 1)
        else:
            last_non_pad_token = -1
            logger.warning_once(
                f"{self.__class__.__name__} will not detect padding tokens in `inputs_embeds`. Results may be "
                "unexpected if using padding tokens in conjunction with `inputs_embeds.`"
            )

        pooled_logits = logits[torch.arange(batch_size, device=logits.device), last_non_pad_token]

        loss = None
        if labels is not None:
            loss = self.loss_function(logits=logits, labels=labels, pooled_logits=pooled_logits, config=self.config)

        return SequenceClassifierOutput(
            loss=loss,
            logits=pooled_logits,
            hidden_states=hidden_states,
            attentions=attentions,
        )