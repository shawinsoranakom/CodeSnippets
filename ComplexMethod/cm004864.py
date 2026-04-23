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
        """
        This method overrides [~generation.utils.GenerationMixin._sample].
        To ease maintenance, modifications are marked with the comment "Csm specific".

        Indeed, Csm model requires a custom generation sampling step:
        1. Infer the backbone model to sample the first codebook token
        2. Call generate on the depth decoder with the first codebook token as input_ids to sample the next codebook tokens
        3. Use these generated codebook tokens as input_ids to sample the next first codebook token using the backbone model
        4. Repeat until stopping criteria is met

        Csm supports two stopping criteria:
        - stop when the generated sequence is at max_length
        - stop when all the generated codebook tokens are the codebook_eos_token_id
        """
        # init values
        # *************** Csm specific ***************
        pad_token_id = self.config.codebook_pad_token_id
        has_eos_stopping_criteria = generation_config._eos_token_tensor is not None
        # ============================================
        output_attentions = generation_config.output_attentions
        output_hidden_states = generation_config.output_hidden_states
        output_scores = generation_config.output_scores
        output_logits = generation_config.output_logits
        return_dict_in_generate = generation_config.return_dict_in_generate
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

        # *************** Csm specific ***************
        if input_ids.ndim == 2 and model_kwargs.get("inputs_embeds") is None:
            # in the case where the passed input_ids correspond to text tokens, i.e. don't have a third dimension for codebook ids,
            # we need to remove the input length to the MaxLengthCriteria stopping criteria has such input are not returned
            for criterion in stopping_criteria:
                if isinstance(criterion, MaxLengthCriteria):
                    criterion.max_length -= cur_len
        # ============================================

        model_forward = (
            self.get_compiled_call(generation_config.compile_config)
            if self._valid_auto_compile_criteria(model_kwargs, generation_config)
            else self.__call__
        )

        # *************** Csm specific ***************
        model_kwargs.update({"output_hidden_states": True})

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
                # prepare variable output controls (note: some models won't accept all output controls)
                model_inputs.update({"output_attentions": output_attentions} if output_attentions else {})
                outputs = model_forward(**model_inputs, return_dict=True)
            prefill_consumed = True

            # synced_gpus: don't waste resources running the code we don't need; kwargs must be updated before skipping
            model_kwargs = self._update_model_kwargs_for_generation(
                outputs,
                model_kwargs,
            )
            if synced_gpus and this_peer_finished:
                continue

            # Clone is needed to avoid keeping a hanging ref to outputs.logits which may be very large for first iteration
            # (the clone itself is always small)
            next_token_logits = outputs.logits[:, -1, :].clone().float()
            next_token_logits = next_token_logits.to(input_ids.device)

            # pre-process distribution
            next_token_scores = logits_processor(input_ids, next_token_logits)

            # Store scores, attentions and hidden_states when required
            if return_dict_in_generate:
                if output_scores:
                    scores += (next_token_scores,)
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

            # *************** Csm specific ***************
            # infer the depth decoder
            first_codebook_ids = next_tokens[:, None]
            # adds place holder in position 0 that will be replaced by the backbone_last_hidden_state
            depth_decoder_input_ids = nn.functional.pad(first_codebook_ids, (1, 0), value=0)
            backbone_last_hidden_state = outputs.hidden_states[-1][:, -1, :]

            depth_decoder_outputs = self.depth_decoder.generate(
                input_ids=depth_decoder_input_ids, backbone_last_hidden_state=backbone_last_hidden_state.clone()
            )
            codebook_ids = (
                depth_decoder_outputs
                if isinstance(depth_decoder_outputs, torch.Tensor)
                else depth_decoder_outputs.sequences
            )
            # remove the place holder in position 0
            codebook_ids = codebook_ids[:, 1:]
            next_tokens = codebook_ids

            # finished sentences should have their next token be a padding token
            if has_eos_stopping_criteria:
                next_tokens = next_tokens * unfinished_sequences.unsqueeze(-1) + pad_token_id * (
                    1 - unfinished_sequences.unsqueeze(-1)
                )

            # update generated ids, model inputs, and length for next step
            if input_ids.ndim == 2:
                input_ids = next_tokens[:, None, :]
            else:
                input_ids = torch.cat([input_ids, next_tokens[:, None, :]], dim=1)
            # ============================================

            if streamer is not None:
                streamer.put(next_tokens.cpu())

            # *************** Csm specific ***************
            # for the eos stopping criteria, is it expected that the eos token is the same for each codebook !!!!
            unfinished_sequences = unfinished_sequences & ~(
                input_ids[:, -1, :-1] == self.config.codebook_eos_token_id
            ).all(-1)
            # ============================================
            unfinished_sequences = unfinished_sequences & ~stopping_criteria(input_ids, scores)
            this_peer_finished = unfinished_sequences.max() == 0
            cur_len += 1

            # This is needed to properly delete outputs.logits which may be very large for first iteration
            # Otherwise a reference to outputs is kept which keeps the logits alive in the next iteration
            del outputs

            # *************** Csm specific ***************
            del depth_decoder_outputs
            # ============================================

        if streamer is not None:
            streamer.end()

        if return_dict_in_generate:
            return GenerateDecoderOnlyOutput(
                sequences=input_ids,
                scores=scores,
                logits=raw_logits,
                attentions=decoder_attentions,
                hidden_states=decoder_hidden_states,
                past_key_values=model_kwargs.get("past_key_values"),
            )
        else:
            return input_ids