def forward(
        self,
        input_ids: torch.LongTensor | None = None,  # text inputs
        pixel_values: torch.FloatTensor | None = None,  # vision inputs
        input_features: torch.FloatTensor | None = None,  # audio inputs
        attention_mask: torch.Tensor | None = None,
        input_features_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        token_type_ids: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        use_cache: bool | None = None,
        **lm_kwargs: Unpack[TransformersKwargs],
    ) -> Gemma3nModelOutputWithPast:
        r"""
        input_features_mask (`torch.Tensor` of shape `(batch_size, sequence_length)`, *optional*):
            Attention mask for `input_features` where non-zero values mark valid audio frames.
        labels (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
            Labels for computing the masked language modeling loss. Indices should either be in `[0, ...,
            config.text_config.vocab_size]` or -100 (see `input_ids` docstring). Tokens with indices set to `-100` are ignored
            (masked), the loss is only computed for the tokens with labels in `[0, ..., config.text_config.vocab_size]`.

        Example:

        ```python
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO
        >>> from transformers import AutoProcessor, Gemma3nForConditionalGeneration

        >>> model = Gemma3nForConditionalGeneration.from_pretrained("google/gemma3n2-3b-mix-224")
        >>> processor = AutoProcessor.from_pretrained("google/gemma3n2-3b-mix-224")

        >>> prompt = "Where is the cat standing?"
        >>> url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/pipeline-cat-chonk.jpeg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> inputs = processor(images=image, text=prompt,  return_tensors="pt")

        >>> # Generate
        >>> generate_ids = model.generate(**inputs,)
        >>> processor.batch_decode(generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
        "Where is the cat standing?\nsnow"
        ```
        """
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if input_ids is not None:
            inputs_embeds = self.get_input_embeddings()(input_ids)

            # Prepare per-layer inputs from inputs_ids
            per_layer_inputs_mask = torch.logical_and(input_ids >= 0, input_ids < self.vocab_size_per_layer_input)
            per_layer_inputs_tokens = torch.where(per_layer_inputs_mask, input_ids, torch.zeros_like(input_ids))
            per_layer_inputs = self.language_model.get_per_layer_inputs(per_layer_inputs_tokens)

            # Handle vision tokens (>= embed_vision.vocab_offset and < embed_audio.vocab_offset)
            vision_mask = torch.logical_and(
                input_ids >= self.embed_vision.vocab_offset, input_ids < self.embed_audio.vocab_offset
            )
            dummy_vision_token_id = self.embed_vision.vocab_offset + self.embed_vision.vocab_size - 1
            vision_input_ids = torch.where(vision_mask, input_ids, dummy_vision_token_id).to(inputs_embeds.device)
            vision_embeds = self.embed_vision(input_ids=vision_input_ids)
            vision_embeds = vision_embeds.to(inputs_embeds.device, inputs_embeds.dtype)
            expanded_vision_mask = vision_mask.unsqueeze(-1).expand_as(inputs_embeds)
            inputs_embeds = torch.where(expanded_vision_mask, vision_embeds, inputs_embeds)

            # Handle audio tokens (>= embed_audio.vocab_offset)
            audio_mask = input_ids >= self.embed_audio.vocab_offset
            dummy_audio_token_id = self.embed_audio.vocab_offset + self.embed_audio.vocab_size - 1
            audio_input_ids = torch.where(audio_mask, input_ids, dummy_audio_token_id).to(inputs_embeds.device)
            audio_embeds = self.embed_audio(input_ids=audio_input_ids)
            audio_embeds = audio_embeds.to(inputs_embeds.device, inputs_embeds.dtype)
            expanded_audio_mask = audio_mask.unsqueeze(-1).expand_as(inputs_embeds)
            inputs_embeds = torch.where(expanded_audio_mask, audio_embeds, inputs_embeds)
        else:
            per_layer_inputs = None

        # Merge text and images
        if pixel_values is not None:
            image_features = self.get_image_features(pixel_values, return_dict=True).pooler_output
            image_features = image_features.to(inputs_embeds.device, inputs_embeds.dtype)
            special_image_mask, _ = self.get_placeholder_mask(
                input_ids, inputs_embeds=inputs_embeds, image_features=image_features
            )
            inputs_embeds = inputs_embeds.masked_scatter(special_image_mask, image_features)

        # Merge text and audio
        if input_features is not None and input_features_mask is not None:
            audio_outputs = self.get_audio_features(input_features, ~input_features_mask, return_dict=True)
            audio_features = audio_outputs.pooler_output
            audio_mask = audio_outputs.audio_mel_mask

            # The Gemma3nProcessor expects all audio will be 30s in length and inserts 188 audio soft tokens into the
            # text to account for this. However, the audio preprocessing and encoder do not gurarantee they will
            # produce 188 soft tokens; they will produce at most that many tokens, but they may produce fewer tokens
            # depending on the length of the longest audio input in the batch. When we encounter this situation, we pad
            # the audio feature out to 188 soft tokens with the emebedding of the last token in the embed_audio vocab.
            audio_padding_toks = torch.tensor([[self.vocab_size - 1]], dtype=torch.long, device=audio_features.device)
            audio_padding_embs = self.embed_audio(input_ids=audio_padding_toks)
            audio_features = torch.where(audio_mask.unsqueeze(-1), audio_padding_embs, audio_features)

            audio_batch_size, audio_seq_len, audio_embed_dim = audio_features.shape
            extra_padding_tokens = self.config.audio_soft_tokens_per_image - audio_seq_len
            extra_padding_features = audio_padding_embs.expand(audio_batch_size, extra_padding_tokens, audio_embed_dim)

            audio_features = torch.cat((audio_features, extra_padding_features), dim=1)
            audio_features = audio_features.to(inputs_embeds.device, inputs_embeds.dtype)
            _, special_audio_mask = self.get_placeholder_mask(
                input_ids, inputs_embeds=inputs_embeds, audio_features=audio_features
            )
            inputs_embeds = inputs_embeds.masked_scatter(special_audio_mask, audio_features)

        outputs = self.language_model(
            input_ids=None,
            per_layer_inputs=per_layer_inputs,
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            use_cache=use_cache,
            return_dict=True,
            **lm_kwargs,
        )

        return Gemma3nModelOutputWithPast(
            last_hidden_state=outputs.last_hidden_state,
            past_key_values=outputs.past_key_values if use_cache else None,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
            image_hidden_states=image_features if pixel_values is not None else None,
            audio_hidden_states=audio_features if input_features is not None else None,
        )