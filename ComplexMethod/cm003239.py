def generate_with_fallback(
        self,
        segment_input,
        decoder_input_ids,
        cur_bsz,
        seek,
        batch_idx_map,
        temperatures,
        generation_config,
        logits_processor,
        stopping_criteria,
        prefix_allowed_tokens_fn,
        synced_gpus,
        return_token_timestamps,
        do_condition_on_prev_tokens,
        is_shortform,
        batch_size,
        attention_mask,
        kwargs,
    ):
        kwargs = copy.copy(kwargs)

        # 6.6 Batch generate current chunk
        seek_sequence_list = [None for _ in range(cur_bsz)]
        seek_outputs_list = [None for _ in range(cur_bsz)]
        needs_fallback = [False for _ in range(cur_bsz)]
        should_skip = [False for _ in range(cur_bsz)]
        fallback_index_map = list(range(cur_bsz))
        if generation_config.no_speech_threshold is not None:
            self._setup_no_speech_detection(logits_processor, segment_input, decoder_input_ids, kwargs)

        for fallback_idx, temperature in enumerate(temperatures):
            generation_config.do_sample = temperature is not None and temperature > 0.0
            generation_config.temperature = temperature if generation_config.do_sample else 1.0
            if generation_config.do_sample:
                generation_config.num_beams = 1

            generate_kwargs = copy.copy(kwargs)
            for key in ["do_sample", "temperature", "num_beams"]:
                if key in generate_kwargs:
                    del generate_kwargs[key]

            cur_bsz = decoder_input_ids.shape[0]
            if generation_config.cache_implementation == "static" and cur_bsz < batch_size:
                segment_input = F.pad(segment_input, (0, 0, 0, 0, 0, batch_size - cur_bsz), value=0)
                decoder_input_ids = F.pad(
                    decoder_input_ids, (0, 0, 0, batch_size - cur_bsz), value=generation_config.pad_token_id
                )
                if generate_kwargs.get("decoder_attention_mask") is not None:
                    generate_kwargs["decoder_attention_mask"] = F.pad(
                        generate_kwargs["decoder_attention_mask"], (0, 0, 0, batch_size - cur_bsz), value=True
                    )
                if generate_kwargs.get("encoder_outputs") is not None:
                    generate_kwargs["encoder_outputs"] = F.pad(
                        generate_kwargs["encoder_outputs"], (0, 0, 0, 0, 0, batch_size - cur_bsz), value=0
                    )

            seek_outputs = super().generate(
                segment_input,
                generation_config=generation_config,
                logits_processor=logits_processor,
                stopping_criteria=stopping_criteria,
                prefix_allowed_tokens_fn=prefix_allowed_tokens_fn,
                synced_gpus=synced_gpus,
                decoder_input_ids=decoder_input_ids,
                attention_mask=attention_mask,
                **generate_kwargs,
            )

            model_output_type = type(seek_outputs)

            # post-process sequence tokens and outputs to be in list form
            seek_sequences, seek_outputs = self._postprocess_outputs(
                seek_outputs=seek_outputs,
                decoder_input_ids=decoder_input_ids,
                return_token_timestamps=return_token_timestamps,
                generation_config=generation_config,
                is_shortform=is_shortform,
                seek=seek,
                batch_idx_map=batch_idx_map,
            )

            if cur_bsz < batch_size:
                seek_sequences = seek_sequences[:cur_bsz]
                seek_outputs = seek_outputs[:cur_bsz]

            # 6.7 Extract cut sequences from every sequence and check if fallback should be applied
            # Loop over each decoded audio individually as each decoding can be of a different length
            new_fallback_index_map = []
            new_segment_input = []
            new_decoder_input_ids = []
            new_decoder_attention_mask = []

            for i, seek_sequence in enumerate(seek_sequences):
                # remove all padding tokens, except for the eos token
                if seek_sequence[-1] == generation_config.pad_token_id:
                    num_paddings = (seek_sequence == generation_config.pad_token_id).sum()
                    if generation_config.pad_token_id == generation_config.eos_token_id:
                        # we do not remove the eos token id since it is needed for avg logprob calculation in _need_fallback
                        num_paddings -= 1
                    if num_paddings != 0:
                        seek_sequence = seek_sequence[:-num_paddings]

                # check which sequences in batch need fallback & which should be skipped
                needs_fallback[i], should_skip[i] = self._need_fallback(
                    seek_sequence,
                    seek_outputs,
                    i,
                    logits_processor,
                    generation_config,
                    self.config.vocab_size,
                    temperature,
                )

                # remove eos token
                if seek_sequence[-1] == generation_config.eos_token_id:
                    seek_sequence = seek_sequence[:-1]

                seek_sequence_list[fallback_index_map[i]] = seek_sequence
                seek_outputs_list[fallback_index_map[i]] = seek_outputs[i]
                is_low_temperature = temperature is None or temperature < 0.5
                do_condition_on_prev_tokens[fallback_index_map[i]] = (
                    generation_config.condition_on_prev_tokens and is_low_temperature
                )

                if needs_fallback[i]:
                    new_fallback_index_map.append(fallback_index_map[i])
                    new_segment_input.append(segment_input[i])
                    new_decoder_input_ids.append(decoder_input_ids[i])
                    if "decoder_attention_mask" in kwargs:
                        new_decoder_attention_mask.append(kwargs["decoder_attention_mask"][i])

            fallback_index_map = new_fallback_index_map

            # if no sequence needs to be run with temperature fallback, we're finished
            if len(fallback_index_map) == 0 or fallback_idx == len(temperatures) - 1:
                seek_sequences = seek_sequence_list
                seek_outputs = seek_outputs_list
                break

            # if we're still in the loop, make sure that decoder_input_ids and segment inputs are tensors
            decoder_input_ids = torch.stack(new_decoder_input_ids)
            segment_input = torch.stack(new_segment_input)
            if "decoder_attention_mask" in kwargs:
                kwargs["decoder_attention_mask"] = torch.stack(new_decoder_attention_mask)

        return seek_sequences, seek_outputs, should_skip, do_condition_on_prev_tokens, model_output_type