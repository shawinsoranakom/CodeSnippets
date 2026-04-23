def forward(
        self,
        input_ids: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        encoder_hidden_states: torch.Tensor | None = None,
        encoder_attention_mask: torch.Tensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
        use_cache: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | ProphetNetDecoderLMOutput:
        r"""
        labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Labels for computing the left-to-right language modeling loss (next word prediction). Indices should be in
            `[-100, 0, ..., config.vocab_size]` (see `input_ids` docstring) Tokens with indices set to `-100` are
            ignored (masked), the loss is only computed for the tokens with labels n `[0, ..., config.vocab_size]`

        Example:

        ```python
        >>> from transformers import AutoTokenizer, ProphetNetForCausalLM
        >>> import torch

        >>> tokenizer = AutoTokenizer.from_pretrained("microsoft/prophetnet-large-uncased")
        >>> model = ProphetNetForCausalLM.from_pretrained("microsoft/prophetnet-large-uncased")
        >>> assert model.config.is_decoder, f"{model.__class__} has to be configured as a decoder."
        >>> inputs = tokenizer("Hello, my dog is cute", return_tensors="pt")
        >>> outputs = model(**inputs)

        >>> logits = outputs.logits

        >>> # Model can also be used with EncoderDecoder framework
        >>> from transformers import BertTokenizer, EncoderDecoderModel, AutoTokenizer
        >>> import torch

        >>> tokenizer_enc = BertTokenizer.from_pretrained("google-bert/bert-large-uncased")
        >>> tokenizer_dec = AutoTokenizer.from_pretrained("microsoft/prophetnet-large-uncased")
        >>> model = EncoderDecoderModel.from_encoder_decoder_pretrained(
        ...     "google-bert/bert-large-uncased", "microsoft/prophetnet-large-uncased"
        ... )

        >>> ARTICLE = (
        ...     "the us state department said wednesday it had received no "
        ...     "formal word from bolivia that it was expelling the us ambassador there "
        ...     "but said the charges made against him are `` baseless ."
        ... )
        >>> input_ids = tokenizer_enc(ARTICLE, return_tensors="pt").input_ids
        >>> labels = tokenizer_dec(
        ...     "us rejects charges against its ambassador in bolivia", return_tensors="pt"
        ... ).input_ids
        >>> outputs = model(input_ids=input_ids, decoder_input_ids=labels[:, :-1], labels=labels[:, 1:])

        >>> loss = outputs.loss
        ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        # decoder outputs consists of (dec_features, past_key_values, dec_hidden, dec_attn)
        outputs = self.prophetnet.decoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
            encoder_hidden_states=encoder_hidden_states,
            encoder_attention_mask=encoder_attention_mask,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            use_cache=use_cache,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        batch_size, sequence_length = input_ids.shape if input_ids is not None else inputs_embeds.shape[:2]

        predicting_streams = outputs[1].view(batch_size, self.config.ngram, sequence_length, -1)
        predict_logits = self.lm_head(predicting_streams)

        logits = predict_logits[:, 0]
        logits_ngram = predict_logits[:, 1:] if self.config.ngram > 1 else None

        loss = None
        if labels is not None:
            loss = self._compute_loss(predict_logits, labels)

        if not return_dict:
            all_logits = tuple(v for v in [logits, logits_ngram] if v is not None)
            return (loss,) + all_logits + outputs[2:] if loss is not None else all_logits + outputs[2:]
        else:
            return ProphetNetDecoderLMOutput(
                loss=loss,
                logits=logits,
                logits_ngram=logits_ngram,
                past_key_values=outputs.past_key_values,
                hidden_states=outputs.hidden_states,
                hidden_states_ngram=outputs.hidden_states_ngram,
                attentions=outputs.attentions,
                ngram_attentions=outputs.ngram_attentions,
                cross_attentions=outputs.cross_attentions,
            )