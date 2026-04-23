def _prepare_generated_length(
        self: "GenerativePreTrainedModel",
        generation_config,
        has_default_max_length,
        has_default_min_length,
        model_input_name,
        input_ids_length,
        inputs_tensor,
    ):
        """Prepared max and min length in generation configs to avoid clashes between similar attributes"""

        if generation_config.max_new_tokens is not None:
            if not has_default_max_length and generation_config.max_length is not None:
                logger.warning(
                    f"Both `max_new_tokens` (={generation_config.max_new_tokens}) and `max_length`(="
                    f"{generation_config.max_length}) seem to have been set. `max_new_tokens` will take precedence. "
                    "Please refer to the documentation for more information. "
                    "(https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)"
                )
            generation_config.max_length = generation_config.max_new_tokens + input_ids_length

        # If both `inputs_embeds` and `input_ids` are passed, we correct length with `inputs_tensor.shape`
        # We need to get max_length = inputs_embeds_len + max_new_tokens
        elif (
            model_input_name == "inputs_embeds"
            and input_ids_length != inputs_tensor.shape[1]
            and not self.config.is_encoder_decoder
            and not has_default_max_length
        ):
            generation_config.max_length -= inputs_tensor.shape[1]
        elif has_default_max_length:  # by default let's always generate 20 new tokens
            generation_config.max_length = generation_config.max_length + input_ids_length
            max_position_embeddings = getattr(self.config, "max_position_embeddings", None)
            if max_position_embeddings is not None:
                generation_config.max_length = min(generation_config.max_length, max_position_embeddings)

        # same for min length
        if generation_config.min_new_tokens is not None:
            if not has_default_min_length:
                logger.warning(
                    f"Both `min_new_tokens` (={generation_config.min_new_tokens}) and `min_length`(="
                    f"{generation_config.min_length}) seem to have been set. `min_new_tokens` will take precedence. "
                    "Please refer to the documentation for more information. "
                    "(https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)"
                )
            generation_config.min_length = generation_config.min_new_tokens + input_ids_length

        elif (
            model_input_name == "inputs_embeds"
            and input_ids_length != inputs_tensor.shape[1]
            and not self.config.is_encoder_decoder
        ):
            generation_config.min_length = max(generation_config.min_length - inputs_tensor.shape[1], 0)

        return generation_config