def forward(
        self,
        input_ids: torch.LongTensor | None = None,
        input_features: torch.FloatTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        position_ids: torch.LongTensor | None = None,
        past_key_values: Cache | None = None,
        encoder_past_key_values: Cache | None = None,
        padding_cache: VoxtralRealtimeConv1dPaddingCache | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        encoder_inputs_embeds: torch.FloatTensor | None = None,
        labels: torch.LongTensor | None = None,
        use_cache: bool | None = None,
        logits_to_keep: int | torch.Tensor = 0,
        num_delay_tokens: int | torch.Tensor = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> VoxtralRealtimeCausalLMOutputWithPast:
        r"""
        encoder_past_key_values (`Cache`, *optional*):
            Pre-computed hidden-states (key and value in the self-attention blocks) for the encoder that can be used to speed up sequential decoding.
        padding_cache (`VoxtralRealtimeConv1dPaddingCache`, *optional*):
            Cache for padding in convolutional layers to maintain state across streaming chunks.
        encoder_inputs_embeds (`torch.FloatTensor`, *optional*):
            Optionally, instead of passing `input_features` you can choose to directly pass an embedded representation for the encoder.
        num_delay_tokens (`int` or `torch.Tensor`, *optional*):
            Number of delay tokens used when preparing inputs, see [`~VoxtralRealtimeProcessor`] for more details.

        Example:

        ```python
        >>> import torch
        >>> from transformers import VoxtralRealtimeForConditionalGeneration, AutoProcessor
        >>> from datasets import load_dataset

        >>> repo_id = "mistralai/Voxtral-Mini-4B-Realtime-2602"

        >>> processor = AutoProcessor.from_pretrained(repo_id)
        >>> model = VoxtralRealtimeForConditionalGeneration.from_pretrained(repo_id, dtype=torch.bfloat16, device_map="auto")

        >>> ds = load_dataset("hf-internal-testing/librispeech_asr_dummy", "clean", split="validation")
        >>> audio = ds[0]["audio"]["array"]

        >>> inputs = processor(audio, return_tensors="pt")
        >>> inputs = inputs.to(model.device, dtype=model.dtype)

        >>> outputs = model.generate(**inputs)
        >>> processor.batch_decode(outputs, skip_special_tokens=True)
        ```"""
        if (input_ids is None) ^ (inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_ids or inputs_embeds")

        if (input_features is None) ^ (encoder_inputs_embeds is not None):
            raise ValueError("You must specify exactly one of input_features or encoder_inputs_embeds")

        if inputs_embeds is None:
            inputs_embeds = self.get_input_embeddings()(input_ids)

        if input_features is not None or encoder_inputs_embeds is not None:
            audio_outputs = self.get_audio_features(
                input_features=input_features,
                encoder_inputs_embeds=encoder_inputs_embeds,
                past_key_values=encoder_past_key_values,
                padding_cache=padding_cache,
                use_cache=use_cache,
                return_dict=True,
            )
            inputs_embeds += audio_outputs.pooler_output.to(inputs_embeds.device)

        if num_delay_tokens is None:
            num_delay_tokens = self.config.default_num_delay_tokens
            logger.warning_once(
                f"`num_delay_tokens` was not provided. "
                f"Falling back to `config.default_num_delay_tokens={num_delay_tokens}`. "
                f"Consider preparing inputs with [`~VoxtralRealtimeProcessor.__call__`] which automatically sets this parameter."
            )

        time_tensor = torch.full(
            (1,),
            num_delay_tokens,
            device=inputs_embeds.device,
            dtype=inputs_embeds.dtype,
        )
        t_cond = self.time_embedding(time_tensor)
        t_cond = t_cond[None, ...]  # broadcastable to batch size

        outputs: CausalLMOutputWithPast = self.language_model(
            attention_mask=attention_mask,
            position_ids=position_ids,
            past_key_values=past_key_values,
            inputs_embeds=inputs_embeds,
            labels=labels,
            use_cache=use_cache,
            logits_to_keep=logits_to_keep,
            t_cond=t_cond,
            **kwargs,
        )
        return VoxtralRealtimeCausalLMOutputWithPast(
            loss=outputs.loss,
            logits=outputs.logits,
            past_key_values=outputs.past_key_values,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
            encoder_past_key_values=audio_outputs.past_key_values if use_cache else None,
            padding_cache=audio_outputs.padding_cache if use_cache else None,
        )