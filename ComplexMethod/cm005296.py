def forward(
        self,
        inputs: torch.Tensor | None = None,
        attention_mask: torch.Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        labels: torch.Tensor | None = None,
        return_dict: bool | None = None,
        input_ids: torch.Tensor | None = None,
        **kwargs,
    ) -> tuple | PerceiverMaskedLMOutput:
        r"""
        inputs (`torch.FloatTensor`):
            Inputs to the perceiver. Can be anything: images, text, audio, video, etc.
        labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Labels for computing the masked language modeling loss. Indices should be in `[-100, 0, ...,
            config.vocab_size]` (see `input_ids` docstring) Tokens with indices set to `-100` are ignored (masked), the
            loss is only computed for the tokens with labels in `[0, ..., config.vocab_size]`

        Examples:

        ```python
        >>> from transformers import AutoTokenizer, PerceiverForMaskedLM
        >>> import torch

        >>> tokenizer = AutoTokenizer.from_pretrained("deepmind/language-perceiver")
        >>> model = PerceiverForMaskedLM.from_pretrained("deepmind/language-perceiver")

        >>> # training
        >>> text = "This is an incomplete sentence where some words are missing."
        >>> inputs = tokenizer(text, padding="max_length", return_tensors="pt")
        >>> # mask " missing."
        >>> inputs["input_ids"][0, 52:61] = tokenizer.mask_token_id
        >>> labels = tokenizer(text, padding="max_length", return_tensors="pt").input_ids

        >>> outputs = model(**inputs, labels=labels)
        >>> loss = outputs.loss
        >>> round(loss.item(), 2)
        19.87

        >>> logits = outputs.logits
        >>> list(logits.shape)
        [1, 2048, 262]

        >>> # inference
        >>> text = "This is an incomplete sentence where some words are missing."
        >>> encoding = tokenizer(text, padding="max_length", return_tensors="pt")

        >>> # mask bytes corresponding to " missing.". Note that the model performs much better if the masked span starts with a space.
        >>> encoding["input_ids"][0, 52:61] = tokenizer.mask_token_id

        >>> # forward pass
        >>> with torch.no_grad():
        ...     outputs = model(**encoding)
        >>> logits = outputs.logits
        >>> list(logits.shape)
        [1, 2048, 262]

        >>> masked_tokens_predictions = logits[0, 52:61].argmax(dim=-1).tolist()
        >>> tokenizer.decode(masked_tokens_predictions)
        ' missing.'
        ```"""
        if inputs is not None and input_ids is not None:
            raise ValueError("You cannot use both `inputs` and `input_ids`")
        elif inputs is None and input_ids is not None:
            inputs = input_ids

        return_dict = return_dict if return_dict is not None else self.config.return_dict

        outputs = self.perceiver(
            inputs=inputs,
            attention_mask=attention_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        logits = self.embedding_decoder(
            outputs.logits if return_dict else outputs[0], embedding_layer=self.perceiver.input_preprocessor.embeddings
        )

        masked_lm_loss = None
        if labels is not None:
            loss_fct = CrossEntropyLoss()  # -100 index = padding token
            masked_lm_loss = loss_fct(logits.view(-1, self.config.vocab_size), labels.view(-1))

        if not return_dict:
            output = (logits,) + outputs[2:]
            return ((masked_lm_loss,) + output) if masked_lm_loss is not None else output

        return PerceiverMaskedLMOutput(
            loss=masked_lm_loss,
            logits=logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
            cross_attentions=outputs.cross_attentions,
        )