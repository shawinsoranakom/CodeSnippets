def _prepare_encoder_hidden_states_kwargs_for_generation(
        self,
        inputs_tensor: torch.Tensor,
        model_kwargs,
        model_input_name: str | None,
        generation_config: GenerationConfig,
    ) -> dict[str, Any]:
        encoder_hidden_states = None
        # attention mask is consumed once to produce text conditional hidden states through the text encoder
        encoder_attention_mask = model_kwargs.pop("attention_mask")
        guidance_scale = generation_config.guidance_scale

        # 1. condition on text
        if inputs_tensor is not None:
            encoder = self.get_encoder()
            # Compatibility with Accelerate big model inference: we need the encoder to outputs stuff on the same device
            # as the inputs.
            if hasattr(encoder, "_hf_hook"):
                encoder._hf_hook.io_same_device = True

            # Prepare args and kwargs from model kwargs.
            irrelevant_prefix = ["decoder_", "use_cache"]
            encoder_kwargs = {
                argument: value
                for argument, value in model_kwargs.items()
                if not any(argument.startswith(p) for p in irrelevant_prefix)
            }
            encoder_signature = set(inspect.signature(encoder.forward).parameters)
            encoder_accepts_wildcard = "kwargs" in encoder_signature or "model_kwargs" in encoder_signature
            if not encoder_accepts_wildcard:
                encoder_kwargs = {
                    argument: value for argument, value in encoder_kwargs.items() if argument in encoder_signature
                }
            encoder_kwargs["output_attentions"] = generation_config.output_attentions
            encoder_kwargs["output_hidden_states"] = generation_config.output_hidden_states

            # make sure that encoder returns `ModelOutput`
            model_input_name = model_input_name if model_input_name is not None else self.text_encoder.main_input_name
            encoder_kwargs["return_dict"] = True
            encoder_kwargs[model_input_name] = inputs_tensor
            if encoder_attention_mask is not None:
                encoder_kwargs["attention_mask"] = encoder_attention_mask
            encoder_hidden_states = encoder(**encoder_kwargs).last_hidden_state

            # optionally project encoder_hidden_states
            if self.text_encoder.config.hidden_size != self.decoder.config.hidden_size:
                encoder_hidden_states = self.enc_to_dec_proj(encoder_hidden_states)

            # for classifier free guidance we need to add a 'null' input to our encoder hidden states
            if guidance_scale is not None and guidance_scale > 1:
                encoder_hidden_states = torch.concatenate(
                    [encoder_hidden_states, torch.zeros_like(encoder_hidden_states)], dim=0
                )
                if encoder_attention_mask is not None:
                    encoder_attention_mask = torch.concatenate(
                        [encoder_attention_mask, torch.zeros_like(encoder_attention_mask)], dim=0
                    )
            if encoder_attention_mask is not None:
                encoder_hidden_states = encoder_hidden_states * encoder_attention_mask[..., None]

        # 2. condition on audio
        audio_hidden_states = model_kwargs.get("input_features", None)

        if inputs_tensor is not None:
            if audio_hidden_states is not None:
                null_audio_hidden_states = torch.zeros_like(audio_hidden_states)
            else:
                null_audio_hidden_states = torch.zeros(
                    (inputs_tensor.shape[0], 1, self.config.num_chroma), device=self.device, dtype=self.dtype
                )
            null_audio_hidden_states[:, :, 0] = 1

            if audio_hidden_states is None:
                audio_hidden_states = null_audio_hidden_states

        if audio_hidden_states is not None:
            # for classifier free guidance we need to add a 'null' input to our audio hidden states
            if guidance_scale is not None and guidance_scale > 1:
                audio_hidden_states = torch.concatenate([audio_hidden_states, null_audio_hidden_states], dim=0)

            # optionally project audio_hidden_states ->
            # (batch_size, seq_len, num_chroma) -> (batch_size, seq_len, hidden_size)
            if self.config.num_chroma != self.decoder.config.hidden_size:
                audio_hidden_states = self.audio_enc_to_dec_proj(audio_hidden_states)

            # pad or truncate to config.chroma_length
            if audio_hidden_states.shape[1] < self.config.chroma_length:
                n_repeat = int(math.ceil(self.config.chroma_length / audio_hidden_states.shape[1]))
                audio_hidden_states = audio_hidden_states.repeat(1, n_repeat, 1)
            audio_hidden_states = audio_hidden_states[:, : self.config.chroma_length]

            if encoder_hidden_states is not None:
                encoder_hidden_states = torch.cat([audio_hidden_states, encoder_hidden_states], dim=1)
            else:
                encoder_hidden_states = audio_hidden_states

        model_kwargs["encoder_hidden_states"] = encoder_hidden_states

        return model_kwargs