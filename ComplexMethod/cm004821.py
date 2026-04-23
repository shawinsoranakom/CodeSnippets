def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        decoder_input_ids: torch.LongTensor | None = None,
        decoder_attention_mask: torch.LongTensor | None = None,
        encoder_outputs: tuple[tuple[torch.FloatTensor]] | None = None,
        global_attention_mask: torch.FloatTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        decoder_inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        use_cache: bool | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor] | LEDSeq2SeqLMOutput:
        r"""
        decoder_input_ids (`torch.LongTensor` of shape `(batch_size, target_sequence_length)`, *optional*):
            Indices of decoder input sequence tokens in the vocabulary.

            Indices can be obtained using [`LedTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            [What are input IDs?](../glossary#input-ids)

            LED uses the `eos_token_id` as the starting token for `decoder_input_ids` generation. If `past_key_values`
            is used, optionally only the last `decoder_input_ids` have to be input (see `past_key_values`).
        decoder_attention_mask (`torch.LongTensor` of shape `(batch_size, target_sequence_length)`, *optional*):
            Default behavior: generate a tensor that ignores pad tokens in `decoder_input_ids`. Causal mask will also
            be used by default.

            If you want to change padding behavior, you should read [`modeling_led._prepare_decoder_inputs`] and modify
            to your needs. See diagram 1 in [the paper](https://huggingface.co/papers/1910.13461) for more information on the
            default strategy.
        global_attention_mask (`torch.FloatTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Mask to decide the attention given on each token, local attention or global attention for the encoder.
            Tokens with global attention attends to all other tokens, and all other tokens attend to them. This is
            important for task-specific finetuning because it makes the model more flexible at representing the task.
            For example, for classification, the <s> token should be given global attention. For QA, all question
            tokens should also have global attention. Please refer to the [Longformer
            paper](https://huggingface.co/papers/2004.05150) for more details. Mask values selected in `[0, 1]`:

            - 0 for local attention (a sliding window attention),
            - 1 for global attention (tokens that attend to all other tokens, and all other tokens attend to them).
        labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Labels for computing the masked language modeling loss. Indices should either be in `[0, ...,
            config.vocab_size]` or -100 (see `input_ids` docstring). Tokens with indices set to `-100` are ignored
            (masked), the loss is only computed for the tokens with labels in `[0, ..., config.vocab_size]`.

        Example Summarization:

        ```python
        >>> import torch
        >>> from transformers import AutoTokenizer, LEDForConditionalGeneration

        >>> model = LEDForConditionalGeneration.from_pretrained("allenai/led-large-16384-arxiv")
        >>> tokenizer = AutoTokenizer.from_pretrained("allenai/led-large-16384-arxiv")

        >>> ARTICLE_TO_SUMMARIZE = '''Transformers (Vaswani et al., 2017) have achieved state-of-the-art
        ...     results in a wide range of natural language tasks including generative language modeling
        ...     (Dai et al., 2019; Radford et al., 2019) and discriminative ... language understanding (Devlin et al., 2019).
        ...     This success is partly due to the self-attention component which enables the network to capture contextual
        ...     information from the entire sequence. While powerful, the memory and computational requirements of
        ...     self-attention grow quadratically with sequence length, making it infeasible (or very expensive) to
        ...     process long sequences. To address this limitation, we present Longformer, a modified Transformer
        ...     architecture with a self-attention operation that scales linearly with the sequence length, making it
        ...     versatile for processing long documents (Fig 1). This is an advantage for natural language tasks such as
        ...     long document classification, question answering (QA), and coreference resolution, where existing approaches
        ...     partition or shorten the long context into smaller sequences that fall within the typical 512 token limit
        ...     of BERT-style pretrained models. Such partitioning could potentially result in loss of important
        ...     cross-partition information, and to mitigate this problem, existing methods often rely on complex
        ...     architectures to address such interactions. On the other hand, our proposed Longformer is able to build
        ...     contextual representations of the entire context using multiple layers of attention, reducing the need for
        ...     task-specific architectures.'''
        >>> inputs = tokenizer.encode(ARTICLE_TO_SUMMARIZE, return_tensors="pt")

        >>> # Global attention on the first token (cf. Beltagy et al. 2020)
        >>> global_attention_mask = torch.zeros_like(inputs)
        >>> global_attention_mask[:, 0] = 1

        >>> # Generate Summary
        >>> summary_ids = model.generate(inputs, global_attention_mask=global_attention_mask, num_beams=3, max_length=32)
        >>> print(tokenizer.decode(summary_ids[0], skip_special_tokens=True, clean_up_tokenization_spaces=True))
        ```

        Example Conditional generation :

        ```python
        >>> from transformers import AutoTokenizer, LEDForConditionalGeneration

        >>> tokenizer = AutoTokenizer.from_pretrained("allenai/led-base-16384")
        >>> TXT = "My friends are <mask> but they eat too many carbs."

        >>> model = LEDForConditionalGeneration.from_pretrained("allenai/led-base-16384")
        >>> input_ids = tokenizer([TXT], return_tensors="pt")["input_ids"]

        >>> prediction = model.generate(input_ids)[0]
        >>> print(tokenizer.decode(prediction, skip_special_tokens=True))
        ```
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if labels is not None:
            if use_cache:
                logger.warning("The `use_cache` argument is changed to `False` since `labels` is provided.")
            use_cache = False
            if decoder_input_ids is None and decoder_inputs_embeds is None:
                decoder_input_ids = shift_tokens_right(
                    labels, self.config.pad_token_id, self.config.decoder_start_token_id
                )

        outputs = self.led(
            input_ids,
            attention_mask=attention_mask,
            decoder_input_ids=decoder_input_ids,
            decoder_attention_mask=decoder_attention_mask,
            encoder_outputs=encoder_outputs,
            global_attention_mask=global_attention_mask,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            decoder_inputs_embeds=decoder_inputs_embeds,
            use_cache=use_cache,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        lm_logits = self.lm_head(outputs[0]) + self.final_logits_bias

        masked_lm_loss = None
        if labels is not None:
            loss_fct = CrossEntropyLoss()
            masked_lm_loss = loss_fct(lm_logits.view(-1, self.config.vocab_size), labels.view(-1))

        if not return_dict:
            output = (lm_logits,) + outputs[1:]
            return ((masked_lm_loss,) + output) if masked_lm_loss is not None else output

        return LEDSeq2SeqLMOutput(
            loss=masked_lm_loss,
            logits=lm_logits,
            past_key_values=outputs.past_key_values,
            decoder_hidden_states=outputs.decoder_hidden_states,
            decoder_attentions=outputs.decoder_attentions,
            cross_attentions=outputs.cross_attentions,
            encoder_last_hidden_state=outputs.encoder_last_hidden_state,
            encoder_hidden_states=outputs.encoder_hidden_states,
            encoder_attentions=outputs.encoder_attentions,
            encoder_global_attentions=outputs.encoder_global_attentions,
        )