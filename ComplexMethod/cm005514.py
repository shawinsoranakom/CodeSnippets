def _get_logits_processor(
        self: "GenerativePreTrainedModel",
        generation_config: GenerationConfig,
        input_ids_seq_length: int | None = None,
        encoder_input_ids: torch.LongTensor | None = None,
        prefix_allowed_tokens_fn: Callable[[int, torch.Tensor], list[int]] | None = None,
        logits_processor: LogitsProcessorList | None = None,
        device: str | None = None,
        model_kwargs: dict[str, Any] | None = None,
        negative_prompt_ids: torch.Tensor | None = None,
        negative_prompt_attention_mask: torch.Tensor | None = None,
    ) -> LogitsProcessorList:
        """
        This class returns a [`LogitsProcessorList`] list object that contains all relevant [`LogitsProcessor`]
        instances used to modify the scores of the language model head.
        """
        # instantiate processors list
        processors = LogitsProcessorList()
        if logits_processor is None:
            logits_processor = []

        if generation_config.guidance_scale is not None and generation_config.guidance_scale != 1:
            processors.append(
                UnbatchedClassifierFreeGuidanceLogitsProcessor(
                    generation_config.guidance_scale,
                    self,
                    unconditional_ids=negative_prompt_ids,
                    unconditional_attention_mask=negative_prompt_attention_mask,
                    use_cache=generation_config.use_cache,
                )
            )
        if generation_config.sequence_bias is not None:
            processors.append(SequenceBiasLogitsProcessor(sequence_bias=generation_config.sequence_bias))

        if (
            generation_config.encoder_repetition_penalty is not None
            and generation_config.encoder_repetition_penalty != 1.0
        ):
            if encoder_input_ids is not None and len(encoder_input_ids.shape) == 2:
                processors.append(
                    EncoderRepetitionPenaltyLogitsProcessor(
                        penalty=generation_config.encoder_repetition_penalty,
                        encoder_input_ids=encoder_input_ids,
                    )
                )
            else:
                warnings.warn(
                    "Passing `encoder_repetition_penalty` requires some form of `input_ids` to be passed to "
                    "`generate`, ignoring the argument.",
                    UserWarning,
                )
        if generation_config.repetition_penalty is not None and generation_config.repetition_penalty != 1.0:
            processors.append(RepetitionPenaltyLogitsProcessor(penalty=generation_config.repetition_penalty))
        if generation_config.no_repeat_ngram_size is not None and generation_config.no_repeat_ngram_size > 0:
            processors.append(NoRepeatNGramLogitsProcessor(generation_config.no_repeat_ngram_size))
        if (
            generation_config.encoder_no_repeat_ngram_size is not None
            and generation_config.encoder_no_repeat_ngram_size > 0
        ):
            if encoder_input_ids is not None and len(encoder_input_ids.shape) == 2:
                processors.append(
                    EncoderNoRepeatNGramLogitsProcessor(
                        generation_config.encoder_no_repeat_ngram_size,
                        encoder_input_ids,
                    )
                )
            else:
                warnings.warn(
                    "Passing `encoder_no_repeat_ngram_size` requires some form of `input_ids` to be passed to "
                    "`generate`, ignoring the argument.",
                    UserWarning,
                )
        if generation_config.bad_words_ids is not None:
            processors.append(
                NoBadWordsLogitsProcessor(
                    generation_config.bad_words_ids,
                    generation_config._eos_token_tensor,
                )
            )
        if (
            generation_config.min_length is not None
            and getattr(generation_config, "_eos_token_tensor", None) is not None
            and generation_config.min_length > 0
        ):
            processors.append(
                MinLengthLogitsProcessor(
                    generation_config.min_length,
                    generation_config._eos_token_tensor,
                    device=device,
                )
            )
        if (
            generation_config.min_new_tokens is not None
            and getattr(generation_config, "_eos_token_tensor", None) is not None
            and generation_config.min_new_tokens > 0
        ):
            processors.append(
                MinNewTokensLengthLogitsProcessor(
                    input_ids_seq_length,
                    generation_config.min_new_tokens,
                    generation_config._eos_token_tensor,
                    device=device,
                )
            )
        if prefix_allowed_tokens_fn is not None:
            processors.append(
                PrefixConstrainedLogitsProcessor(
                    prefix_allowed_tokens_fn,
                    generation_config.num_beams,
                )
            )
        if generation_config.forced_bos_token_id is not None:
            processors.append(
                ForcedBOSTokenLogitsProcessor(
                    generation_config.forced_bos_token_id,
                )
            )
        if generation_config.forced_eos_token_id is not None:
            processors.append(
                ForcedEOSTokenLogitsProcessor(
                    generation_config.max_length,
                    generation_config.forced_eos_token_id,
                    device=device,
                )
            )
        if generation_config.remove_invalid_values is True:
            processors.append(InfNanRemoveLogitsProcessor())
        if generation_config.exponential_decay_length_penalty is not None:
            processors.append(
                ExponentialDecayLengthPenalty(
                    generation_config.exponential_decay_length_penalty,
                    generation_config._eos_token_tensor,
                    input_ids_seq_length,
                )
            )
        if generation_config.suppress_tokens is not None:
            processors.append(
                SuppressTokensLogitsProcessor(
                    generation_config.suppress_tokens,
                    device=device,
                )
            )
        if generation_config.begin_suppress_tokens is not None:
            begin_index = input_ids_seq_length
            begin_index = (
                begin_index
                if (input_ids_seq_length > 1 or generation_config.forced_bos_token_id is None)
                else begin_index + 1
            )
            processors.append(
                SuppressTokensAtBeginLogitsProcessor(
                    generation_config.begin_suppress_tokens,
                    begin_index,
                    device=device,
                )
            )

        # TODO (joao): find a strategy to specify the order of the processors
        processors = self._merge_criteria_processor_list(processors, logits_processor)

        # Processors previously known as `LogitsWarpers`, only applied with sampling strategies
        if generation_config.do_sample:
            # In beam methods, we need to keep at least one non-eos token to explore continuations that might have a
            # better score (i.e. keep len(list(generation_config._eos_token_tensor)) + 1)
            if generation_config.num_beams is not None and generation_config.num_beams > 1:
                if isinstance(generation_config._eos_token_tensor, list):
                    min_tokens_to_keep = len(generation_config._eos_token_tensor) + 1
                elif isinstance(generation_config._eos_token_tensor, torch.Tensor):
                    min_tokens_to_keep = generation_config._eos_token_tensor.shape[0] + 1
                else:
                    min_tokens_to_keep = 2
            else:
                min_tokens_to_keep = 1

            # the following idea is largely copied from this PR: https://github.com/huggingface/transformers/pull/5420/files
            # all samplers can be found in `generation_utils_samplers.py`
            if generation_config.temperature is not None and generation_config.temperature != 1.0:
                processors.append(TemperatureLogitsWarper(generation_config.temperature))
            if generation_config.top_h is not None:
                processors.append(TopHLogitsWarper(top_h=generation_config.top_h))
            if generation_config.top_k is not None and generation_config.top_k != 0:
                processors.append(
                    TopKLogitsWarper(top_k=generation_config.top_k, min_tokens_to_keep=min_tokens_to_keep)
                )
            if generation_config.top_p is not None and generation_config.top_p < 1.0:
                processors.append(
                    TopPLogitsWarper(top_p=generation_config.top_p, min_tokens_to_keep=min_tokens_to_keep)
                )
            if generation_config.min_p is not None:
                # Applied after temperature scaling (see https://github.com/ggerganov/llama.cpp/pull/3841#issuecomment-2073826084)
                processors.append(
                    MinPLogitsWarper(min_p=generation_config.min_p, min_tokens_to_keep=min_tokens_to_keep)
                )
            if generation_config.typical_p is not None and generation_config.typical_p < 1.0:
                processors.append(
                    TypicalLogitsWarper(mass=generation_config.typical_p, min_tokens_to_keep=min_tokens_to_keep)
                )
            if generation_config.epsilon_cutoff is not None and 0.0 < generation_config.epsilon_cutoff < 1.0:
                processors.append(
                    EpsilonLogitsWarper(
                        epsilon=generation_config.epsilon_cutoff, min_tokens_to_keep=min_tokens_to_keep
                    )
                )
            if generation_config.eta_cutoff is not None and 0.0 < generation_config.eta_cutoff < 1.0:
                processors.append(
                    EtaLogitsWarper(
                        epsilon=generation_config.eta_cutoff, min_tokens_to_keep=min_tokens_to_keep, device=device
                    )
                )

        # Watermarking should be after all logits processing is finished (see #34630)
        if generation_config.watermarking_config is not None:
            processors.append(
                generation_config.watermarking_config.construct_processor(
                    self.config.get_text_config().vocab_size, device
                )
            )

        # `LogitNormalization` should always be the last logit processor, when present
        if generation_config.renormalize_logits is True:
            processors.append(LogitNormalization())
        return processors