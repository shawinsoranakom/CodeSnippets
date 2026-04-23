def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        decoder_input_ids: torch.Tensor | None = None,
        decoder_attention_mask: torch.BoolTensor | None = None,
        encoder_outputs: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.Tensor | None = None,
        decoder_inputs_embeds: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
        use_cache: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | ProphetNetSeq2SeqLMOutput:
        r"""
        decoder_input_ids (`torch.LongTensor` of shape `(batch_size, target_sequence_length)`, *optional*):
            Indices of decoder input sequence tokens in the vocabulary.

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            [What are decoder input IDs?](../glossary#decoder-input-ids)

            ProphetNet uses the `eos_token_id` as the starting token for `decoder_input_ids` generation. If
            `past_key_values` is used, optionally only the last `decoder_input_ids` have to be input (see
            `past_key_values`).
        decoder_attention_mask (`torch.BoolTensor` of shape `(batch_size, target_sequence_length)`, *optional*):
            Default behavior: generate a tensor that ignores pad tokens in `decoder_input_ids`. Causal mask will also
            be used by default.
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the sequence classification/regression loss. Indices should be in `[-100, 0, ...,
            config.vocab_size - 1]`. All labels set to `-100` are ignored (masked), the loss is only computed for
            labels in `[0, ..., config.vocab_size]`

        Example:

        ```python
        >>> from transformers import AutoTokenizer, ProphetNetForConditionalGeneration

        >>> tokenizer = AutoTokenizer.from_pretrained("microsoft/prophetnet-large-uncased")
        >>> model = ProphetNetForConditionalGeneration.from_pretrained("microsoft/prophetnet-large-uncased")

        >>> input_ids = tokenizer(
        ...     "Studies have been shown that owning a dog is good for you", return_tensors="pt"
        ... ).input_ids  # Batch size 1
        >>> decoder_input_ids = tokenizer("Studies show that", return_tensors="pt").input_ids  # Batch size 1
        >>> outputs = model(input_ids=input_ids, decoder_input_ids=decoder_input_ids)

        >>> logits_next_token = outputs.logits  # logits to predict next token as usual
        >>> logits_ngram_next_tokens = outputs.logits_ngram  # logits to predict 2nd, 3rd, ... next tokens
        ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if labels is not None and decoder_input_ids is None and decoder_inputs_embeds is None:
            # get decoder inputs from shifting lm labels to the right
            decoder_input_ids = self._shift_right(labels)

        outputs = self.prophetnet(
            input_ids=input_ids,
            attention_mask=attention_mask,
            decoder_input_ids=decoder_input_ids,
            decoder_attention_mask=decoder_attention_mask,
            encoder_outputs=encoder_outputs,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            decoder_inputs_embeds=decoder_inputs_embeds,
            use_cache=use_cache,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        batch_size, sequence_length = (
            decoder_input_ids.shape if decoder_input_ids is not None else decoder_inputs_embeds.shape[:2]
        )

        predicting_streams = outputs[1].view(batch_size, self.config.ngram, sequence_length, -1)
        predict_logits = self.lm_head(predicting_streams)

        logits = predict_logits[:, 0]
        logits_ngram = predict_logits[:, 1:] if self.config.ngram > 1 else None

        # To use .view in loss computation, make sure that logits is contiguous.
        if not logits.is_contiguous():
            logits = logits.contiguous()

        loss = None
        if labels is not None:
            loss = self._compute_loss(predict_logits, labels)

        if not return_dict:
            all_logits = tuple(v for v in [logits, logits_ngram] if v is not None)
            return (loss,) + all_logits + outputs[2:] if loss is not None else all_logits + outputs[2:]
        else:
            return ProphetNetSeq2SeqLMOutput(
                loss=loss,
                logits=logits,
                logits_ngram=logits_ngram,
                past_key_values=outputs.past_key_values,
                decoder_hidden_states=outputs.decoder_hidden_states,
                decoder_ngram_hidden_states=outputs.decoder_ngram_hidden_states,
                decoder_attentions=outputs.decoder_attentions,
                decoder_ngram_attentions=outputs.decoder_ngram_attentions,
                cross_attentions=outputs.cross_attentions,
                encoder_last_hidden_state=outputs.encoder_last_hidden_state,
                encoder_hidden_states=outputs.encoder_hidden_states,
                encoder_attentions=outputs.encoder_attentions,
            )