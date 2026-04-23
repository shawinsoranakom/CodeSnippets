def _prefill(
        self: "GenerativePreTrainedModel",
        input_ids: torch.LongTensor,
        generation_config: GenerationConfig,
        model_kwargs: dict,
        is_first_iteration: bool = True,
    ):
        """
        Perform the prefill stage of generation.

        Note that usually, the prefill stage is always the first iteration of a new input batch, and thus multimodal inputs etc
        should be treated as if it's the first iteration. However, for assisted decoding, assistants call `generate`
        several time in a row for a same batch of inputs, so we need to pass `is_first_iteration` here for such cases.
        """
        # When restarting from previous cache, the `input_ids` are either the FULL sequence, including previous inputs,
        # or only the new tokens but in this case the attention_mask still contains the FULL sequence (because otherwise we may
        # lose some early padding tokens information). So slice inputs according to that if needed
        # When restarting from `inputs_embeds`, it's always the FULL sequence, and we always need to slice
        next_sequence_length = None
        inputs_embeds = model_kwargs.get("inputs_embeds")
        use_inputs_embeds = False
        if not self.config.is_encoder_decoder and inputs_embeds is not None and is_first_iteration:
            use_inputs_embeds = True
        if (cache := model_kwargs.get("past_key_values")) is not None:
            past_length = cache.get_seq_length()
            # It will be sliced as input_embeds = inputs_embeds[:, -next_sequence_length:, :] in `prepare_inputs_for_generation`
            if use_inputs_embeds:
                next_sequence_length = model_kwargs["inputs_embeds"].shape[1] - past_length
            else:
                attention_mask_key = "decoder_attention_mask" if self.config.is_encoder_decoder else "attention_mask"
                attention_mask = model_kwargs.get(attention_mask_key)
                # In this case we need to slice - if it's smaller than the mask, only the new inputs were passed -> no need to do anything
                if attention_mask is not None and input_ids.shape[1] == attention_mask.shape[1]:
                    # inputs will be sliced as `input_ids[:, -next_sequence_length :]` in `prepare_inputs_for_generation`
                    next_sequence_length = input_ids.shape[1] - past_length

        # Usual prefill
        if generation_config.prefill_chunk_size is None:
            model_inputs = self.prepare_inputs_for_generation(
                input_ids,
                next_sequence_length=next_sequence_length,
                is_first_iteration=is_first_iteration,
                **model_kwargs,
            )
            return self(**model_inputs, return_dict=True)

        # Chunked prefill (for very large contexts)
        else:
            # Even if we are not compiling the forward, flex is always compiled when used. With chunked prefill, we may
            # end up needing just a bit more graphs than the default (which is 8). Doing this avoids very cryptic warnings
            getattr(torch, "_dynamo").config.cache_size_limit = 64

            chunk_size = generation_config.prefill_chunk_size
            input_chunks = torch.split(input_ids, chunk_size, dim=-1)

            if "past_key_values" not in model_kwargs:
                raise ValueError("Cannot use prefill chunking without a cache")

            model_forward = (
                self.get_compiled_call(generation_config.compile_config)
                if self._valid_auto_compile_criteria(model_kwargs, generation_config)
                else self.__call__
            )

            attention_mask = model_kwargs.pop("attention_mask", None)
            position_ids = model_kwargs.pop("position_ids", None)
            past_length = 0
            for input_chunk in input_chunks:
                current_length = past_length + input_chunk.shape[-1]
                if attention_mask is not None:
                    model_kwargs["attention_mask"] = attention_mask[:, :current_length]
                if position_ids is not None:
                    model_kwargs["position_ids"] = position_ids[:, past_length:current_length]
                model_inputs = self.prepare_inputs_for_generation(input_chunk, **model_kwargs)

                outputs = model_forward(**model_inputs, return_dict=True)

                model_kwargs["past_key_values"] = outputs.past_key_values
                past_length = current_length

            # Recreate the kwargs based on the full length
            model_kwargs["attention_mask"] = attention_mask
            model_kwargs["position_ids"] = position_ids

            # Latest outputs contain next token logits
            return outputs