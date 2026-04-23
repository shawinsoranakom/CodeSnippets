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
    ) -> TokenClassifierOutput:
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

        loss = None
        if labels is not None:
            loss = self.loss_function(logits, labels, self.config)

        return TokenClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=hidden_states,
            attentions=attentions,
        )