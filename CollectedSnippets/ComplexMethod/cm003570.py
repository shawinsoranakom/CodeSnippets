def forward(
        self,
        input_ids: Tensor | None = None,
        attention_mask: Tensor | None = None,
        token_type_ids: Tensor | None = None,
        inputs_embeds: Tensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> DPRQuestionEncoderOutput | tuple[Tensor, ...]:
        r"""
        input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
            Indices of input sequence tokens in the vocabulary. To match pretraining, DPR input sequence should be
            formatted with [CLS] and [SEP] tokens as follows:

            (a) For sequence pairs (for a pair title+text for example):

            ```
            tokens:         [CLS] is this jack ##son ##ville ? [SEP] no it is not . [SEP]
            token_type_ids:   0   0  0    0    0     0       0   0   1  1  1  1   1   1
            ```

            (b) For single sequences (for a question for example):

            ```
            tokens:         [CLS] the dog is hairy . [SEP]
            token_type_ids:   0   0   0   0  0     0   0
            ```

            DPR is a model with absolute position embeddings so it's usually advised to pad the inputs on the right
            rather than the left.

            Indices can be obtained using [`AutoTokenizer`]. See [`PreTrainedTokenizer.encode`] and
            [`PreTrainedTokenizer.__call__`] for details.

            [What are input IDs?](../glossary#input-ids)

        Examples:

        ```python
        >>> from transformers import DPRQuestionEncoder, DPRQuestionEncoderTokenizer

        >>> tokenizer = DPRQuestionEncoderTokenizer.from_pretrained("facebook/dpr-question_encoder-single-nq-base")
        >>> model = DPRQuestionEncoder.from_pretrained("facebook/dpr-question_encoder-single-nq-base")
        >>> input_ids = tokenizer("Hello, is my dog cute ?", return_tensors="pt")["input_ids"]
        >>> embeddings = model(input_ids).pooler_output
        ```
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if input_ids is not None and inputs_embeds is not None:
            raise ValueError("You cannot specify both input_ids and inputs_embeds at the same time")
        elif input_ids is not None:
            self.warn_if_padding_and_no_attention_mask(input_ids, attention_mask)
            input_shape = input_ids.size()
        elif inputs_embeds is not None:
            input_shape = inputs_embeds.size()[:-1]
        else:
            raise ValueError("You have to specify either input_ids or inputs_embeds")

        device = input_ids.device if input_ids is not None else inputs_embeds.device

        if attention_mask is None:
            attention_mask = (
                torch.ones(input_shape, device=device)
                if input_ids is None
                else (input_ids != self.config.pad_token_id)
            )
        if token_type_ids is None:
            token_type_ids = torch.zeros(input_shape, dtype=torch.long, device=device)

        outputs = self.question_encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            inputs_embeds=inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        if not return_dict:
            return outputs[1:]
        return DPRQuestionEncoderOutput(
            pooler_output=outputs.pooler_output, hidden_states=outputs.hidden_states, attentions=outputs.attentions
        )