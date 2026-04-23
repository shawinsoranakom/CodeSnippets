def _sample(
        self,
        input_ids: torch.LongTensor,
        logits_processor: LogitsProcessorList,
        stopping_criteria: StoppingCriteriaList,
        generation_config: GenerationConfig,
        synced_gpus: bool = False,
        streamer: Optional["BaseStreamer"] = None,
        **model_kwargs,
    ) -> GenerateNonBeamOutput | torch.LongTensor:
        output_attentions = generation_config.output_attentions
        output_hidden_states = generation_config.output_hidden_states
        output_scores = generation_config.output_scores
        output_logits = generation_config.output_logits
        return_dict_in_generate = generation_config.return_dict_in_generate
        has_eos_stopping_criteria = any(hasattr(criteria, "eos_token_id") for criteria in stopping_criteria)
        do_sample = generation_config.do_sample

        # init attention / hidden states / scores tuples
        scores = () if (return_dict_in_generate and output_scores) else None
        raw_logits = () if (return_dict_in_generate and output_logits) else None
        decoder_attentions = () if (return_dict_in_generate and output_attentions) else None
        decoder_hidden_states = () if (return_dict_in_generate and output_hidden_states) else None

        # keep track of which sequences are already finished
        batch_size, cur_len = input_ids.shape[:2]
        this_peer_finished = False
        unfinished_sequences = torch.ones(batch_size, dtype=torch.long, device=input_ids.device)

        model_forward = (
            self.get_compiled_call(generation_config.compile_config)
            if self._valid_auto_compile_criteria(model_kwargs, generation_config)
            else self.__call__
        )

        prefill_consumed = False
        outputs = self._prefill(
            input_ids,
            generation_config,
            model_kwargs,
            is_first_iteration=not generation_config.is_assistant,
        )

        while self._has_unfinished_sequences(this_peer_finished, synced_gpus, device=input_ids.device):
            if prefill_consumed:
                next_sequence_length = 1 if model_kwargs["use_cache"] else None
                model_inputs = self.prepare_inputs_for_generation(
                    input_ids, next_sequence_length=next_sequence_length, **model_kwargs
                )
                with self._optimize_model_for_decode():
                    outputs = model_forward(**model_inputs, return_dict=True)
            prefill_consumed = True
            model_kwargs = self._update_model_kwargs_for_generation(
                outputs,
                model_kwargs,
                is_encoder_decoder=self.config.is_encoder_decoder,
            )
            if synced_gpus and this_peer_finished:
                continue

            # Copy is needed to avoid keeping a hanging ref to outputs.logits which may be very large for first iteration
            # (the clone itself is always small)
            next_token_logits = outputs.logits[:, -1, :].to(copy=True, dtype=torch.float32, device=input_ids.device)

            # pre-process distribution (delay pattern reshapes to per-codebook, then warpers apply per-codebook)
            next_token_scores = logits_processor(input_ids, next_token_logits)

            # ===========================
            # BELOW DIFFERENCES WITH GenerationMixin._sample()
            # Store scores, attentions and hidden_states when required
            if return_dict_in_generate:
                if output_scores:
                    scores += (
                        next_token_scores.reshape(batch_size, self.config.num_codebooks, self.config.codebook_size),
                    )
                if output_logits:
                    raw_logits += (next_token_logits,)
                if output_attentions:
                    decoder_attentions += (outputs.attentions,)
                if output_hidden_states:
                    decoder_hidden_states += (outputs.hidden_states,)

            # token selection
            if do_sample:
                probs = nn.functional.softmax(next_token_scores, dim=-1)
                # TODO (joao): this OP throws "skipping cudagraphs due to ['incompatible ops']", find solution
                next_tokens = torch.multinomial(probs, num_samples=1).squeeze(1)
            else:
                next_tokens = torch.argmax(next_token_scores, dim=-1)

            next_token_logits = next_token_logits.reshape(-1, self.config.num_codebooks, self.config.codebook_size)
            next_tokens = next_tokens.reshape(batch_size, self.config.num_codebooks)

            ras_win_len = generation_config.ras_win_len if hasattr(generation_config, "ras_win_len") else None
            ras_win_max_num_repeat = (
                generation_config.ras_win_max_num_repeat
                if hasattr(generation_config, "ras_win_max_num_repeat")
                else None
            )
            audio_input_ids = model_kwargs.get("audio_input_ids")
            if ras_win_len is not None and ras_win_max_num_repeat is not None and audio_input_ids is not None:
                # check if there are repetitions over a window of tokens.
                audio_inputs_ids_window = audio_input_ids[:, -ras_win_len:, :]
                repetition_mask = audio_inputs_ids_window == next_tokens.unsqueeze(1)

                # avoid counting the repetition of the audio stream EOS and BOS tokens
                not_excluded_mask = (audio_inputs_ids_window != self.config.audio_stream_bos_id) & (
                    audio_inputs_ids_window != self.config.audio_stream_eos_id
                )
                repetition_mask = repetition_mask & not_excluded_mask
                rep_num = repetition_mask.sum(dim=1)

                # if we saw repeated tokens in the most recent window of tokens, resample without temperature.
                replacement_mask = rep_num >= ras_win_max_num_repeat
                replacement_tokens = (
                    next_token_logits[replacement_mask].softmax(dim=-1).multinomial(1, replacement=True).view(-1)
                )
                next_tokens[replacement_mask] = replacement_tokens

            # finished sentences should have their next token be a padding token
            if has_eos_stopping_criteria:
                next_tokens = next_tokens * unfinished_sequences[:, None] + self.config.audio_stream_eos_id * (
                    1 - unfinished_sequences[:, None]
                )

            has_audio_stream_eos = (next_tokens == self.config.audio_stream_eos_id).any(dim=-1)
            has_all_audio_stream_eos = (next_tokens == self.config.audio_stream_eos_id).all(dim=-1)
            next_tokens = next_tokens[:, None, :]

            if audio_input_ids is not None:
                model_kwargs["audio_input_ids"] = torch.cat([audio_input_ids, next_tokens], dim=1)
            else:
                model_kwargs["audio_input_ids"] = next_tokens

            next_audio_input_ids_mask = torch.ones((batch_size, 1), dtype=torch.bool, device=next_tokens.device)
            next_audio_input_ids_mask[has_all_audio_stream_eos] = 0
            audio_input_ids_mask = model_kwargs.get("audio_input_ids_mask")
            if audio_input_ids_mask is not None:
                model_kwargs["audio_input_ids_mask"] = torch.cat(
                    [audio_input_ids_mask, next_audio_input_ids_mask], dim=1
                )
            else:
                model_kwargs["audio_input_ids_mask"] = next_audio_input_ids_mask

            # generation of a stream eos audio token will start delay pattern masking in the logits processor
            # for that, we need to set next text token to audio_eos_start_delay_token_id
            next_tokens_flat = input_ids.new_ones(batch_size) * self.config.audio_token_id
            next_tokens_flat[has_audio_stream_eos | (input_ids[:, -1] == self.config.audio_delay_token_id)] = (
                self.config.audio_delay_token_id
            )
            if self.config.eos_token_id is not None:
                next_tokens_flat[has_all_audio_stream_eos] = self.config.eos_token_id
            next_tokens = next_tokens_flat
            # ============================

            # update generated ids, model inputs, and length for next step
            input_ids = torch.cat([input_ids, next_tokens[:, None]], dim=-1)
            if streamer is not None:
                streamer.put(next_tokens.cpu())

            unfinished_sequences = unfinished_sequences & ~stopping_criteria(input_ids, scores)
            this_peer_finished = unfinished_sequences.max() == 0
            cur_len += 1

            # This is needed to properly delete outputs.logits which may be very large for first iteration
            # Otherwise a reference to outputs is kept which keeps the logits alive in the next iteration
            del outputs

        if streamer is not None:
            streamer.end()

        if return_dict_in_generate:
            return HiggsAudioV2GenerationOutput(
                sequences=input_ids,
                scores=scores,
                logits=raw_logits,
                attentions=decoder_attentions,
                hidden_states=decoder_hidden_states,
                past_key_values=model_kwargs.get("past_key_values"),
                audio_sequences=model_kwargs.get("audio_input_ids"),
            )
        else:
            return model_kwargs.get("audio_input_ids")