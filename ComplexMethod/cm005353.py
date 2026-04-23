def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        xpath_tags_seq: torch.LongTensor | None = None,
        xpath_subs_seq: torch.LongTensor | None = None,
        attention_mask: torch.FloatTensor | None = None,
        token_type_ids: torch.LongTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> tuple | BaseModelOutputWithPooling:
        r"""
        xpath_tags_seq (`torch.LongTensor` of shape `(batch_size, sequence_length, config.max_depth)`, *optional*):
            Tag IDs for each token in the input sequence, padded up to config.max_depth.
        xpath_subs_seq (`torch.LongTensor` of shape `(batch_size, sequence_length, config.max_depth)`, *optional*):
            Subscript IDs for each token in the input sequence, padded up to config.max_depth.

        Examples:

        ```python
        >>> from transformers import AutoProcessor, MarkupLMModel

        >>> processor = AutoProcessor.from_pretrained("microsoft/markuplm-base")
        >>> model = MarkupLMModel.from_pretrained("microsoft/markuplm-base")

        >>> html_string = "<html> <head> <title>Page Title</title> </head> </html>"

        >>> encoding = processor(html_string, return_tensors="pt")

        >>> outputs = model(**encoding)
        >>> last_hidden_states = outputs.last_hidden_state
        >>> list(last_hidden_states.shape)
        [1, 4, 768]
        ```"""
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
            attention_mask = torch.ones(input_shape, device=device)

        if token_type_ids is None:
            token_type_ids = torch.zeros(input_shape, dtype=torch.long, device=device)

        extended_attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)
        extended_attention_mask = extended_attention_mask.to(dtype=self.dtype)
        extended_attention_mask = (1.0 - extended_attention_mask) * -10000.0

        embedding_output = self.embeddings(
            input_ids=input_ids,
            xpath_tags_seq=xpath_tags_seq,
            xpath_subs_seq=xpath_subs_seq,
            position_ids=position_ids,
            token_type_ids=token_type_ids,
            inputs_embeds=inputs_embeds,
        )
        encoder_outputs = self.encoder(
            embedding_output,
            extended_attention_mask,
            **kwargs,
        )
        sequence_output = encoder_outputs[0]
        pooled_output = self.pooler(sequence_output) if self.pooler is not None else None

        return BaseModelOutputWithPooling(
            last_hidden_state=sequence_output,
            pooler_output=pooled_output,
        )