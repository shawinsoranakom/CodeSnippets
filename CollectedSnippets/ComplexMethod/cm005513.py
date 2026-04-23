def _get_candidate_generator(
        self: "GenerativePreTrainedModel",
        generation_config: GenerationConfig,
        input_ids: torch.LongTensor,
        inputs_tensor: torch.Tensor,
        logits_processor: LogitsProcessorList,
        model_kwargs: dict[str, Any],
        assistant_model: Optional["PreTrainedModel"] = None,
        target_tokenizer: Optional["PreTrainedTokenizerBase"] = None,
        assistant_tokenizer: Optional["PreTrainedTokenizerBase"] = None,
    ) -> CandidateGenerator:
        """
        Returns the candidate generator to be used in `assisted_generation`
        """
        different_tokenizers = all(v is not None for v in (assistant_model, target_tokenizer, assistant_tokenizer))

        if generation_config.assistant_early_exit is not None:
            candidate_generator = EarlyExitCandidateGenerator(
                input_ids=input_ids,
                assistant_model=self,
                generation_config=generation_config,
                model_kwargs=model_kwargs,
                inputs_tensor=inputs_tensor,
                logits_processor=logits_processor,
            )
        elif generation_config.prompt_lookup_num_tokens is not None:
            candidate_generator = PromptLookupCandidateGenerator(
                eos_token_id=generation_config._eos_token_tensor,
                num_output_tokens=generation_config.prompt_lookup_num_tokens,
                max_matching_ngram_size=generation_config.max_matching_ngram_size or 2,
                max_length=generation_config.max_length,
                logits_processor=logits_processor,
                vocab_size=self.config.get_text_config().vocab_size,
            )
        elif different_tokenizers:
            assistant_model = cast("PreTrainedModel", assistant_model)
            target_tokenizer = cast("PreTrainedTokenizerBase", target_tokenizer)
            assistant_tokenizer = cast("PreTrainedTokenizerBase", assistant_tokenizer)
            if generation_config.do_sample is True:
                atm_translator = AssistantVocabTranslatorCache.get_translator(
                    target_tokenizer,
                    assistant_tokenizer,
                    self.config.get_text_config().vocab_size,
                    assistant_model=assistant_model,
                    assistant_prune_lm_head=True,  # prune LM head of assistant model
                )
                # Since we prune the LM head, we cannot use the repetition penalty on the assistant model due to mismatches between token ids and logits index
                assistant_model.generation_config.repetition_penalty = None
                candidate_generator = UniversalSpeculativeDecodingGenerator(
                    input_ids=input_ids,
                    assistant_model=assistant_model,
                    generation_config=generation_config,
                    model_kwargs=model_kwargs,
                    inputs_tensor=inputs_tensor,
                    logits_processor=logits_processor,
                    target_tokenizer=target_tokenizer,
                    assistant_tokenizer=assistant_tokenizer,
                    atm_translator=atm_translator,
                )
            elif generation_config.do_sample is False:
                candidate_generator = AssistedCandidateGeneratorDifferentTokenizers(
                    input_ids=input_ids,
                    assistant_model=assistant_model,
                    generation_config=generation_config,
                    model_kwargs=model_kwargs,
                    inputs_tensor=inputs_tensor,
                    logits_processor=logits_processor,
                    target_tokenizer=target_tokenizer,
                    assistant_tokenizer=assistant_tokenizer,
                )
            else:
                raise ValueError(
                    f"Invalid value for `do_sample`: expected a boolean, got {type(generation_config.do_sample).__name__}"
                )
        else:
            candidate_generator = AssistedCandidateGenerator(
                input_ids=input_ids,
                assistant_model=assistant_model,
                generation_config=generation_config,
                model_kwargs=model_kwargs,
                inputs_tensor=inputs_tensor,
                logits_processor=logits_processor,
            )
        return candidate_generator