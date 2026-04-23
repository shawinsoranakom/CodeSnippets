def _assisted_decoding(
        self: "GenerativePreTrainedModel",
        input_ids: torch.LongTensor,
        logits_processor: LogitsProcessorList,
        stopping_criteria: StoppingCriteriaList,
        generation_config: GenerationConfig,
        synced_gpus: bool = False,
        streamer: Optional["BaseStreamer"] = None,
        inputs_tensor: torch.FloatTensor | None = None,
        assistant_model: Optional["PreTrainedModel"] = None,
        assistant_tokenizer: Optional["PreTrainedTokenizerBase"] = None,
        tokenizer: Optional["PreTrainedTokenizerBase"] = None,
        **model_kwargs,
    ) -> GenerateNonBeamOutput | torch.LongTensor:
        r"""
        Generates sequences of token ids for models with a language modeling head using **greedy decoding** or
        **sample** (depending on `do_sample`), assisted by candidate sequences. Assisted generation is an example of a
        candidate decoding strategy. Can be used for text-decoder, text-to-text, speech-to-text, and vision-to-text
        models.

        Parameters:
            input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
                The sequence used as a prompt for the generation.
            logits_processor (`LogitsProcessorList`):
                An instance of [`LogitsProcessorList`]. List of instances of class derived from [`LogitsProcessor`]
                used to modify the prediction scores of the language modeling head applied at each generation step.
            stopping_criteria (`StoppingCriteriaList`):
                An instance of [`StoppingCriteriaList`]. List of instances of class derived from [`StoppingCriteria`]
                used to tell if the generation loop should stop.
            generation_config ([`~generation.GenerationConfig`]):
                The generation configuration to be used as parametrization of the decoding method.
            synced_gpus (`bool`):
                Whether to continue running the while loop until max_length (needed to avoid deadlocking with
                `FullyShardedDataParallel` and DeepSpeed ZeRO Stage 3).
            streamer (`BaseStreamer`, *optional*):
                Streamer object that will be used to stream the generated sequences. Generated tokens are passed
                through `streamer.put(token_ids)` and the streamer is responsible for any further processing.
            inputs_tensor (`torch.FloatTensor`, *optional*):
                The input tensor for generation. For decoder models, usually `input_ids`. For encoder-decoder models,
                the tensor that produced `model_kwargs["encoder_outputs"]`.
            assistant_model (`PreTrainedModel`, *optional*):
                The model used to assist the generation process. If not provided, the main model will be used.
            assistant_tokenizer (`PreTrainedTokenizerBase`, *optional*):
                The tokenizer used for the assistant model. If not provided, the token space is assumed to be the same.
            tokenizer (`PreTrainedTokenizerBase`, *optional*):
                The tokenizer used for the main model. If not provided, the token space is assumed to be the same.
            model_kwargs:
                Additional model specific keyword arguments will be forwarded to the `forward` function of the model.
                If model is an encoder-decoder model the kwargs should include `encoder_outputs`.

        Return:
            [`~generation.GenerateDecoderOnlyOutput`], [`~generation.GenerateEncoderDecoderOutput`] or
            `torch.LongTensor`: A `torch.LongTensor` containing the generated tokens (default behaviour) or a
            [`~generation.GenerateDecoderOnlyOutput`] if `model.config.is_encoder_decoder=False` and
            `return_dict_in_generate=True` or a [`~generation.GenerateEncoderDecoderOutput`] if
            `model.config.is_encoder_decoder=True`.
        """
        # The cache must be dynamic for assisted generation, and the check must happen AFTER preparing cache
        if not model_kwargs["use_cache"]:
            raise ValueError("assisted generate requires `use_cache=True`")
        if (
            generation_config.cache_implementation in ["static", "hybrid", "sliding_window"]
            or type(model_kwargs.get("past_key_values")) is StaticCache
        ):
            raise ValueError("assisted generate is not supported with Static cache classes`")
        # Get the candidate generator, given the parameterization
        candidate_generator = self._get_candidate_generator(
            generation_config=generation_config,
            input_ids=input_ids,
            inputs_tensor=inputs_tensor,
            assistant_model=assistant_model,
            logits_processor=logits_processor,
            target_tokenizer=tokenizer,
            assistant_tokenizer=assistant_tokenizer,
            model_kwargs=model_kwargs,
        )
        # init values
        do_sample = generation_config.do_sample
        output_attentions = generation_config.output_attentions
        output_hidden_states = generation_config.output_hidden_states
        output_scores = generation_config.output_scores
        output_logits = generation_config.output_logits
        return_dict_in_generate = generation_config.return_dict_in_generate

        # init attention / hidden states / scores tuples
        scores = () if (return_dict_in_generate and output_scores) else None
        raw_logits = () if (return_dict_in_generate and output_logits) else None
        decoder_attentions = () if (return_dict_in_generate and output_attentions) else None
        cross_attentions = () if (return_dict_in_generate and output_attentions) else None
        decoder_hidden_states = () if (return_dict_in_generate and output_hidden_states) else None

        # if model is an encoder-decoder, retrieve encoder attention weights and hidden states
        if return_dict_in_generate and self.config.is_encoder_decoder:
            encoder_attentions = model_kwargs["encoder_outputs"].get("attentions") if output_attentions else None
            encoder_hidden_states = (
                model_kwargs["encoder_outputs"].get("hidden_states") if output_hidden_states else None
            )

        # keep track of which sequences are already finished
        batch_size, cur_len = input_ids.shape[:2]
        if batch_size > 1:
            raise ValueError("assisted generate is only supported for batch_size = 1")
        unfinished_sequences = torch.ones(batch_size, dtype=torch.long, device=input_ids.device)

        this_peer_finished = False
        is_first_iteration = True  # to preserve the same API in the output as other generation methods
        while self._has_unfinished_sequences(this_peer_finished, synced_gpus, device=input_ids.device):
            cur_len = input_ids.shape[1]

            #  1. Fetch candidate sequences from a `CandidateGenerator` and move to the correct device
            candidate_input_ids, candidate_logits = candidate_generator.get_candidates(input_ids)
            candidate_input_ids = candidate_input_ids.to(self.device)
            if candidate_logits is not None:
                candidate_logits = candidate_logits.to(self.device)

            candidate_length = candidate_input_ids.shape[1] - input_ids.shape[1]
            is_done_candidate = stopping_criteria(candidate_input_ids, None)

            # 2. Use the original model to obtain the next token logits given the candidate sequence. We obtain
            # `candidate_length + 1` relevant logits from this process: in the event that all candidates are correct,
            # we use this forward pass to also pick the subsequent logits in the original model.

            # 2.1. Prepare the model inputs
            candidate_kwargs = copy.copy(model_kwargs)
            candidate_kwargs = _prepare_attention_mask(
                candidate_kwargs, candidate_input_ids.shape[1], self.config.is_encoder_decoder
            )
            candidate_kwargs = _prepare_token_type_ids(candidate_kwargs, candidate_input_ids.shape[1])
            if (position_ids := candidate_kwargs.get("position_ids")) is not None and candidate_length > 0:
                new_length = candidate_length + position_ids.shape[-1]
                candidate_kwargs = _prepare_position_ids(candidate_kwargs, new_length, self.config.is_encoder_decoder)

            next_sequence_length = candidate_length + 1 if not is_first_iteration else None
            model_inputs = self.prepare_inputs_for_generation(
                candidate_input_ids,
                next_sequence_length=next_sequence_length,
                is_first_iteration=is_first_iteration,
                **candidate_kwargs,
            )

            if "logits_to_keep" in model_inputs:
                model_inputs["logits_to_keep"] = candidate_length + 1

            # 2.2. Run a forward pass on the candidate sequence

            outputs = self(**model_inputs)

            # 2.3. Process the new logits
            # .float() is needed to retain precision for later logits manipulations
            new_logits = outputs.logits[:, -candidate_length - 1 :].to(
                dtype=torch.float32, device=input_ids.device
            )  # excludes the input prompt if present
            next_token_logits = new_logits.clone()
            if len(logits_processor) > 0:
                for i in range(candidate_length + 1):
                    new_logits[:, i, :] = logits_processor(candidate_input_ids[:, : cur_len + i], new_logits[:, i, :])

            # 3. Select the accepted tokens. There are two possible cases:
            # Case 1: `do_sample=True` and we have logits for the candidates (originally from speculative decoding)
            # 👉 Apply algorithm 1 from the speculative decoding paper (https://huggingface.co/papers/2211.17192).
            if do_sample and candidate_logits is not None:
                valid_tokens, n_matches = _speculative_sampling(
                    candidate_input_ids,
                    candidate_logits,
                    candidate_length,
                    new_logits,
                    is_done_candidate,
                )

            # Case 2: all other cases (originally from assisted generation) 👉 Compare the tokens selected from the
            # original model logits with the candidate tokens. We can keep the candidate tokens until the first
            # mismatch, or until the max length is reached.
            else:
                if do_sample:
                    probs = new_logits.softmax(dim=-1)
                    selected_tokens = torch.multinomial(probs[0, :, :], num_samples=1).squeeze(1)[None, :]
                else:
                    selected_tokens = new_logits.argmax(dim=-1)

                candidate_new_tokens = candidate_input_ids[:, cur_len:]
                n_matches = ((~(candidate_new_tokens == selected_tokens[:, :-1])).cumsum(dim=-1) < 1).sum()

                # Ensure we don't generate beyond max_len or an EOS token
                if is_done_candidate and n_matches == candidate_length:
                    n_matches -= 1
                valid_tokens = selected_tokens[:, : n_matches + 1]

            # 4. Update variables according to the number of matching assistant tokens. Remember: the token generated
            # by the model after the last candidate match is also valid, as it is generated from a correct sequence.
            # Because of this last token, assisted generation search reduces to a normal greedy search/sample if there
            # is no match.

            # 4.1. Get the valid continuation, after the matching tokens
            input_ids = torch.cat((input_ids, valid_tokens), dim=-1)
            if streamer is not None:
                streamer.put(valid_tokens.cpu())
            new_cur_len = input_ids.shape[1]

            # 4.2. Discard past key values relative to unused assistant tokens
            outputs.past_key_values.crop(new_cur_len - 1)

            # 5. Update the candidate generation strategy if needed
            candidate_generator.update_candidate_strategy(input_ids, new_logits, n_matches)

            # synced_gpus: don't waste resources running the code we don't need; kwargs must be updated before skipping
            model_kwargs = self._update_model_kwargs_for_generation(
                outputs,
                model_kwargs,
                is_encoder_decoder=self.config.is_encoder_decoder,
                num_new_tokens=n_matches + 1,
            )
            if synced_gpus and this_peer_finished:
                continue

            # Store scores, attentions and hidden_states when required
            # Assistant: modified to append one tuple element per token, as in the other generation methods.
            if return_dict_in_generate:
                newly_added_length = n_matches + 1
                if output_scores:
                    scores += tuple(new_logits[:, i, :] for i in range(newly_added_length))
                if output_logits:
                    raw_logits += tuple(next_token_logits[:, i, :] for i in range(newly_added_length))

                newly_added_length = new_cur_len if is_first_iteration else newly_added_length
                if output_attentions:
                    if self.config.is_encoder_decoder:
                        cross_attentions = _split_model_outputs(
                            cross_attentions, outputs.cross_attentions, cur_len, newly_added_length
                        )
                        decoder_attentions = _split_model_outputs(
                            decoder_attentions,
                            outputs.decoder_attentions,
                            cur_len,
                            newly_added_length,
                            is_decoder_attention=True,
                        )
                    # some (V)LLMs have hard requirement on SDPA and thus never return attn
                    elif outputs.attentions[0] is not None:
                        decoder_attentions = _split_model_outputs(
                            decoder_attentions,
                            outputs.attentions,
                            cur_len,
                            newly_added_length,
                            is_decoder_attention=True,
                        )
                if output_hidden_states:
                    if self.config.is_encoder_decoder:
                        decoder_hidden_states = _split_model_outputs(
                            decoder_hidden_states, outputs.decoder_hidden_states, cur_len, newly_added_length
                        )
                    else:
                        decoder_hidden_states = _split_model_outputs(
                            decoder_hidden_states, outputs.hidden_states, cur_len, newly_added_length
                        )

            unfinished_sequences = unfinished_sequences & ~stopping_criteria(input_ids, scores)
            this_peer_finished = unfinished_sequences.max() == 0
            is_first_iteration = False

        if streamer is not None:
            streamer.end()

        if (
            isinstance(candidate_generator, AssistedCandidateGenerator)
            and candidate_generator.assistant_model.generation_config.num_assistant_tokens_schedule == "heuristic"
        ):
            candidate_generator.assistant_model.generation_config.num_assistant_tokens = (
                candidate_generator.num_assistant_tokens
            )
        if return_dict_in_generate:
            cache = None
            if any(cache_key in model_kwargs for cache_key in ALL_CACHE_NAMES):
                cache_key = next(cache_key for cache_key in ALL_CACHE_NAMES if cache_key in model_kwargs)
                cache = model_kwargs[cache_key]
            if self.config.is_encoder_decoder:
                return GenerateEncoderDecoderOutput(
                    sequences=input_ids,
                    scores=scores,
                    logits=raw_logits,
                    encoder_attentions=encoder_attentions,
                    encoder_hidden_states=encoder_hidden_states,
                    decoder_attentions=decoder_attentions,
                    cross_attentions=cross_attentions,
                    decoder_hidden_states=decoder_hidden_states,
                    past_key_values=cache,
                )
            else:
                return GenerateDecoderOnlyOutput(
                    sequences=input_ids,
                    scores=scores,
                    logits=raw_logits,
                    attentions=decoder_attentions,
                    hidden_states=decoder_hidden_states,
                    past_key_values=cache,
                )
        else:
            return input_ids