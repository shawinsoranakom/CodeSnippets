def _prepare_text_encoder_kwargs_for_generation(
        self,
        inputs_tensor: torch.Tensor,
        model_kwargs,
        model_input_name: str | None,
        generation_config: GenerationConfig,
    ) -> dict[str, Any]:
        # 1. get text encoder
        encoder = self.get_encoder()
        # Compatibility with Accelerate big model inference: we need the encoder to outputs stuff on the same device
        # as the inputs.
        if hasattr(encoder, "_hf_hook"):
            encoder._hf_hook.io_same_device = True

        # 2. Prepare encoder args and encoder kwargs from model kwargs.
        irrelevant_prefix = ["decoder_", "cross_attn", "use_cache"]
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
        guidance_scale = generation_config.guidance_scale

        # 3. make sure that encoder returns `ModelOutput`
        model_input_name = model_input_name if model_input_name is not None else self.text_encoder.main_input_name
        encoder_kwargs["return_dict"] = True
        encoder_kwargs[model_input_name] = inputs_tensor
        last_hidden_state = encoder(**encoder_kwargs).last_hidden_state

        # for classifier free guidance we need to add a 'null' input to our encoder hidden states
        if guidance_scale is not None and guidance_scale > 1:
            last_hidden_state = torch.concatenate([last_hidden_state, torch.zeros_like(last_hidden_state)], dim=0)
            if "attention_mask" in model_kwargs:
                model_kwargs["attention_mask"] = torch.concatenate(
                    [model_kwargs["attention_mask"], torch.zeros_like(model_kwargs["attention_mask"])], dim=0
                )

        model_kwargs["encoder_outputs"] = BaseModelOutput(last_hidden_state=last_hidden_state)

        return model_kwargs