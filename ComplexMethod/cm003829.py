def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        audio_input_ids: torch.LongTensor | None = None,
        attention_mask: torch.LongTensor | None = None,
        audio_input_ids_mask: torch.BoolTensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        use_cache: bool | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> BaseModelOutputWithPast:
        r"""
        audio_input_ids (`torch.LongTensor` of shape `(batch_size, num_audio_frames, num_codebooks)`, *optional*):
            Indices of audio codebook tokens.

            Indices can be obtained using [`HiggsAudioV2TokenizerModel.encode`].
        audio_input_ids_mask (`torch.BoolTensor` of shape `(batch_size, num_audio_frames)`, *optional*):
            Indicates which audio frames in `audio_input_ids` are valid.

        Returns:
            [`~models.modeling_outputs.BaseModelOutputWithPast`]:
                Usual decoder outputs with the placeholder positions already substituted by their corresponding
                audio embeddings.

        Example:

        ```python
        >>> from transformers import AutoProcessor, HiggsAudioV2Model
        >>> import torch
        >>> device = "cuda" if torch.cuda.is_available() else "cpu"
        >>> processor = AutoProcessor.from_pretrained("eustlb/higgs-audio-v2-generation-3B-base", device_map=device)
        >>> model = HiggsAudioV2Model.from_pretrained("eustlb/higgs-audio-v2-generation-3B-base", device_map=device)
        >>> conversation = [
        ...     {
        ...         "role": "system",
        ...         "content": [
        ...             {
        ...                 "type": "text",
        ...                 "text": "Generate audio following instruction."
        ...             }
        ...         ]
        ...     },
        ...     {
        ...         "role": "scene",
        ...         "content": [
        ...             {
        ...                 "type": "text",
        ...                 "text": "Audio is recorded from a quiet room."
        ...             }
        ...         ]
        ...     },
        ...     {
        ...         "role": "user",
        ...         "content": [
        ...             {
        ...                 "type": "text",
        ...                 "text": "It was the night before my birthday. Hooray! It's almost here! It may not be a holiday, but it's the best day of the year."
        ...             }
        ...         ]
        ...     },
        ...     {
        ...         "role": "assistant",
        ...         "content": [
        ...             {
        ...                 "type": "audio",
        ...                 "url": "https://huggingface.co/datasets/eustlb/dummy-audio-samples-higgs/resolve/main/belinda.wav"
        ...             }
        ...         ]
        ...     },
        ...     {
        ...         "role": "user",
        ...         "content": [
        ...             {
        ...                 "type": "text",
        ...                 "text": "The sun rises in the east and sets in the west. This simple fact has been observed by humans for thousands of years."
        ...             }
        ...         ]
        ...     }
        ... ]
        >>> inputs = processor.apply_chat_template(conversation, return_dict=True, tokenize=True, sampling_rate=24000, return_tensors="pt")
        >>> inputs = inputs.to(model.device)
        >>> outputs = model(**inputs)
        ```
        """
        if (input_ids is None) and (inputs_embeds is None) and (audio_input_ids is None):
            raise ValueError("You must specify at least one of input_ids, inputs_embeds, or audio_input_ids")

        if (input_ids is not None) and (inputs_embeds is not None):
            raise ValueError("Only one of input_ids or inputs_embeds can be provided")

        audio_token_mask = self.get_placeholder_mask(input_ids, inputs_embeds, audio_input_ids_mask)

        if input_ids is not None:
            inputs_embeds = self.embed_tokens(input_ids)

        if audio_input_ids is not None:
            audio_embeds = self.embed_audio_tokens(audio_input_ids)

        if inputs_embeds is not None and audio_input_ids is not None:
            audio_embeds = (
                audio_embeds[audio_input_ids_mask.to(audio_embeds.device)]
                if audio_input_ids_mask is not None
                else audio_embeds
            )
            inputs_embeds = inputs_embeds.masked_scatter(
                audio_token_mask[..., None].expand_as(inputs_embeds), audio_embeds.to(inputs_embeds.device)
            )
        elif audio_input_ids is not None:
            inputs_embeds = audio_embeds

        if use_cache and past_key_values is None:
            past_key_values = DynamicCache(config=self.config)

        if position_ids is None:
            past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0
            position_ids = torch.arange(inputs_embeds.shape[1], device=inputs_embeds.device) + past_seen_tokens
            position_ids = position_ids.unsqueeze(0)

        causal_mask = create_causal_mask(
            config=self.config,
            inputs_embeds=inputs_embeds,
            attention_mask=attention_mask,
            past_key_values=past_key_values,
            position_ids=position_ids,
        )

        hidden_states = inputs_embeds
        position_embeddings = self.rotary_emb(hidden_states, position_ids)

        for decoder_layer in self.layers[: self.config.num_hidden_layers]:
            hidden_states = decoder_layer(
                hidden_states,
                attention_mask=causal_mask,
                audio_token_mask=audio_token_mask,
                position_ids=position_ids,
                past_key_values=past_key_values,
                position_embeddings=position_embeddings,
                **kwargs,
            )

        hidden_states = self.norm(hidden_states)
        return BaseModelOutputWithPast(
            last_hidden_state=hidden_states,
            past_key_values=past_key_values,
        )