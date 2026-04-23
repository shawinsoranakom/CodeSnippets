def generate(
        self,
        inputs: torch.Tensor | None = None,
        attention_mask: torch.LongTensor | None = None,
        logits_processor: LogitsProcessorList | None = None,
        **kwargs,
    ):
        # 1. Handle generation config and model kwargs
        # Pop generation_mode first since it's specific to Janus
        generation_mode = kwargs.pop("generation_mode", "text")
        generation_config, model_kwargs = self._prepare_generation_config(
            kwargs.pop("generation_config", None), **kwargs
        )

        # Default to "text" generation if mode isn't provided
        if generation_mode == "text":
            # Set guidance_scale=None to prevent running UnbatchedCFG processor.
            return super().generate(
                inputs=inputs,
                attention_mask=attention_mask,
                generation_config=generation_config,
                guidance_scale=None,
                **model_kwargs,
            )

        # Validate generation mode
        if generation_config.get_generation_mode() not in (GenerationMode.SAMPLE, GenerationMode.GREEDY_SEARCH):
            raise ValueError(
                "Got incompatible mode for Image Generation, should be one of greedy or sampling. "
                "Ensure that beam search is de-activated by setting `num_beams=1`."
            )

        # Validate the configuration and model kwargs
        generation_config.validate()
        self._validate_model_kwargs(model_kwargs.copy())

        # 2. Initialize logit processors
        logits_processor = logits_processor if logits_processor is not None else LogitsProcessorList()

        # Set `use_cache=True` as we will be using input embeds for generation.
        model_kwargs["use_cache"] = True

        if generation_config.guidance_scale is None:
            logger.warning("`guidance_scale` is required for CFG but not provided. Setting to default value of 5.")
            generation_config.guidance_scale = 5
        model_kwargs["guidance_scale"] = generation_config.guidance_scale

        # 3. Prepare model inputs
        input_ids, model_input_name, model_kwargs = self._prepare_model_inputs(
            inputs, generation_config.bos_token_id, model_kwargs
        )
        dtype, device = input_ids.dtype, input_ids.device

        if len(input_ids.shape) != 2:
            raise ValueError(
                f"Expected input ids of shape (batch_size, seq_len), but got {input_ids.shape}"
                "Passing `inputs embeds` is not supported currently."
            )

        # Prepare special tokens which will be used generate internally.
        kwargs_has_attention_mask = attention_mask is not None
        self._prepare_special_tokens(generation_config, kwargs_has_attention_mask, device=input_ids.device)

        # 4. Add CFG processor along with user passed logit processor.
        if generation_config.guidance_scale and generation_config.guidance_scale > 1:
            logits_processor.append(ClassifierFreeGuidanceLogitsProcessor(generation_config.guidance_scale))
            generation_config.guidance_scale = None  # Reset to prevent processor duplication.

        # 5. Prepare logits processor
        logits_processor = self._get_logits_processor(
            generation_config=generation_config,
            input_ids_seq_length=input_ids.shape[1],
            encoder_input_ids=input_ids,
            prefix_allowed_tokens_fn=None,
            logits_processor=logits_processor,
            device=device,
        )

        # 6. Expand inputs for multiple image generations per prompt.
        input_ids, model_kwargs = self._expand_inputs_for_generation(
            input_ids=input_ids,
            attention_mask=attention_mask,
            expand_size=generation_config.num_return_sequences,
            **model_kwargs,
        )

        # 7. Prepare input and model caches
        num_image_tokens = self.model.vision_model.config.num_image_tokens
        batch_size, seq_len = input_ids.shape

        input_tokens = input_ids.repeat(2, 1)  # Double batch size for conditional/unconditional logits
        attention_mask = model_kwargs.pop("attention_mask", None)
        attention_mask = attention_mask.repeat(2, 1)
        model_kwargs["attention_mask"] = attention_mask

        # Mask all the tokens that are neither BOS nor BOI with pad token in the unconditional logits.
        mask = (input_tokens[batch_size:, :] != generation_config.bos_token_id) & (
            input_tokens[batch_size:, :] != generation_config.generation_kwargs["boi_token_id"]
        )
        input_tokens[batch_size:, :].masked_fill_(mask, generation_config.pad_token_id)

        inputs_embeds = self.get_input_embeddings()(input_tokens)

        if model_kwargs.get("past_key_values", None) is None:
            # Prepare cache if not provided.
            model_kwargs["past_key_values"] = self._prepare_static_cache(
                cache_implementation=generation_config.cache_implementation or "static",
                # batch_size should account for both conditional/unconditional input; hence multiplied by 2.
                batch_size=batch_size * 2,
                # we should have at least a cache len of seq_len + num_image_tokens.
                max_cache_len=max(generation_config.max_length, num_image_tokens + seq_len),
                model_kwargs=model_kwargs,
            )

        # Placeholder for generated tokens.
        generated_tokens = torch.zeros((batch_size, num_image_tokens), dtype=dtype, device=device)

        # 8. init attention / hidden states / scores tuples
        output_attentions = generation_config.output_attentions
        output_hidden_states = generation_config.output_hidden_states
        output_scores = generation_config.output_scores
        output_logits = generation_config.output_logits
        return_dict_in_generate = generation_config.return_dict_in_generate

        raw_scores = () if (return_dict_in_generate and output_scores) else None
        raw_logits = () if (return_dict_in_generate and output_logits) else None
        decoder_hidden_states = () if (return_dict_in_generate and output_hidden_states) else None
        decoder_attentions = () if (return_dict_in_generate and output_attentions) else None

        for i in range(num_image_tokens):
            # Set `is_first_iteration=True` to force using `inputs_embeds` instead of `input_ids`.
            # Without this, `prepare_inputs_for_generation` would use `input_ids` (the full prompt)
            # instead of our prepared `inputs_embeds` (1 new token).
            # This causes CUDA error: device-side assert triggered, seen around the call to ` self.self_attn`.
            # Set this to `True` is also necessary to match the expected output, see the more detailed comment
            # https://github.com/huggingface/transformers/pull/45044#discussion_r3020805374.
            model_inputs = self.prepare_inputs_for_generation(
                inputs_embeds=inputs_embeds, input_ids=input_tokens, is_first_iteration=True, **model_kwargs
            )
            if "attention_mask" in model_inputs:
                model_inputs["attention_mask"] = model_inputs["attention_mask"].to(inputs_embeds.device)

            outputs = self.model.language_model(
                **model_inputs,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
            )

            # Update model_kwargs like attention_mask for next generation.
            model_kwargs = self._update_model_kwargs_for_generation(outputs, model_kwargs)
            hidden_state = outputs.last_hidden_state[:, -1, :].clone()

            # Generate scores using the generation head (Not using above defined LM Head)
            scores = self.model.generation_head(hidden_state)
            next_token_scores = logits_processor(input_ids, scores)

            # Sample next token.
            if generation_config.do_sample:
                probs = torch.softmax(next_token_scores, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1).squeeze(-1)
            else:
                next_token = torch.argmax(next_token_scores, dim=-1)

            generated_tokens[:, i] = next_token

            # Prepare embeddings for the next step.
            next_token = torch.cat([next_token, next_token])
            next_token = next_token.unsqueeze(-1)

            inputs_embeds = self.prepare_embeddings_for_image_generation(next_token)

        if return_dict_in_generate:
            if output_scores:
                raw_scores += (scores,)
            if output_logits:
                raw_logits += (hidden_state.float(),)
            if output_attentions:
                decoder_attentions += outputs.attentions
            if output_hidden_states:
                decoder_hidden_states += outputs.hidden_states

        if return_dict_in_generate:
            return GenerateDecoderOnlyOutput(
                sequences=generated_tokens,
                scores=scores,
                logits=raw_logits,
                attentions=decoder_attentions,
                hidden_states=decoder_hidden_states,
                past_key_values=outputs.past_key_values,
            )
        else:
            return generated_tokens