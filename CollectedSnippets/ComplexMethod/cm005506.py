def prepare_inputs_for_generation(
        self: "GenerativePreTrainedModel",
        input_ids: torch.LongTensor,
        next_sequence_length: int | None = None,
        past_key_values: Cache | None = None,
        attention_mask: torch.LongTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        is_first_iteration: bool | None = False,
        **kwargs,
    ):
        """
        Prepare the model inputs for generation. Notable steps include selecting the correct input key and cloning when appropriate,
        creating position_ids from the attention_mask when missing, slicing inputs and converting 2D attention masks to 4D for
        compilable caches, and finally forwarding all additional keyword arguments unchanged to the model's forward pass.

        See the forward pass in the model documentation for expected arguments (different models might have different
        requirements for e.g. `past_key_values`). This function should work as is for most LLMs.
        """
        # Instantiate output
        model_inputs = {}

        # 1. Prepare base model inputs
        input_ids_key = "decoder_input_ids" if self.config.is_encoder_decoder else "input_ids"
        # if `inputs_embeds` are passed, we only want to use them in the 1st generation step for every prompt.
        if not self.config.is_encoder_decoder and inputs_embeds is not None and is_first_iteration:
            model_inputs[input_ids_key] = None
            prompt_embeds = (
                inputs_embeds[:, -next_sequence_length:, :] if next_sequence_length is not None else inputs_embeds
            )
            model_inputs["inputs_embeds"] = prompt_embeds.clone(memory_format=torch.contiguous_format)
            batch_size, sequence_length = prompt_embeds.shape[:2]
        else:
            # `clone` calls in this function ensure a consistent stride. See #32227
            input_ids = input_ids[:, -next_sequence_length:] if next_sequence_length is not None else input_ids
            model_inputs[input_ids_key] = input_ids.clone(memory_format=torch.contiguous_format)
            batch_size, sequence_length = input_ids.shape[:2]  # we slice here as some models may have them 3D

        # 2. Add important inputs
        if past_key_values is not None:
            model_inputs["past_key_values"] = past_key_values
        position_ids_key = "decoder_position_ids" if self.config.is_encoder_decoder else "position_ids"
        if (position_ids := kwargs.pop(position_ids_key, None)) is not None:
            model_inputs[position_ids_key] = position_ids
        if (token_type_ids := kwargs.pop("token_type_ids", None)) is not None:
            model_inputs["token_type_ids"] = token_type_ids

        # 3. Slice model inputs if it's an input that should have the same length as `input_ids`
        for model_input_name in [position_ids_key, "token_type_ids", "mm_token_type_ids"]:
            model_input = model_inputs.get(model_input_name)
            if model_input is not None and model_input.shape[-1] != sequence_length:
                # Input can be 2D or 3D, and we always slice on `seq-length` (last dim)
                model_input = model_input[..., -sequence_length:].clone(memory_format=torch.contiguous_format)
                model_inputs[model_input_name] = model_input

        # 4. Create 4D attention mask is we are using a compilable cache (important for performant compiled forward
        # pass)
        encoder_attention_mask = attention_mask if self.config.is_encoder_decoder else None
        attention_mask_key = "decoder_attention_mask" if self.config.is_encoder_decoder else "attention_mask"
        attention_mask = (
            kwargs.pop("decoder_attention_mask", None) if self.config.is_encoder_decoder else attention_mask
        )
        if (
            isinstance(past_key_values, Cache)
            and past_key_values.is_compileable
            and attention_mask is not None
            and attention_mask.ndim == 2
        ):
            # Some models may overwrite the general one
            causal_mask_creation_function = getattr(self, "create_masks_for_generate", create_masks_for_generate)
            attention_mask = causal_mask_creation_function(
                config=self.config,
                # we only need batch size, seq_length, dtype and device here - so we pass a 0-sized tensor with only the metadata
                inputs_embeds=torch.empty((batch_size, sequence_length, 0), dtype=self.dtype, device=input_ids.device),
                attention_mask=attention_mask,
                past_key_values=model_inputs.get("past_key_values"),
                position_ids=model_inputs.get(position_ids_key),
                # The following kwargs are not used in the main function - only on a few models with overloaded `create_masks_for_generate`
                token_type_ids=model_inputs.get("token_type_ids"),
                mm_token_type_ids=model_inputs.get("mm_token_type_ids"),
                is_first_iteration=is_first_iteration,
            )

        if attention_mask is not None:
            model_inputs[attention_mask_key] = attention_mask

        if encoder_attention_mask is not None:
            model_inputs["attention_mask"] = encoder_attention_mask

        # 5. Forward ALL kwargs that are uninitialized, e.g. `use_cache` (except a few exceptions)
        kwargs_to_avoid_forwarding = ("labels", "next_sequence_length")
        for key, value in kwargs.items():
            if key not in model_inputs and key not in kwargs_to_avoid_forwarding:
                model_inputs[key] = value

        # BC for remote code models only: create `cache_position` on the fly here, as we don't want to maintain them in kwargs
        # between `forward`s
        if self.is_remote_code() and "cache_position" in set(inspect.signature(self.forward).parameters):
            logger.warning_once(
                "The remote code model you are currently using seems to expect `cache_position`. This arg has been "
                "removed from the Transformers library, and will stop being created in `generate` even for remote code models "
                "in a future release. Please open a PR on the remote code hub repo to remove any usage of `cache_position`."
            )
            past_seen_tokens = past_key_values.get_seq_length() if past_key_values is not None else 0
            cache_position = torch.arange(sequence_length, device=input_ids.device) + past_seen_tokens
            model_inputs["cache_position"] = cache_position

        return model_inputs