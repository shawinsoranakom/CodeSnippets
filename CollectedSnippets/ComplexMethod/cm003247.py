def _prepare_decoder_input_ids(
        cur_bsz,
        init_tokens,
        current_segments,
        batch_idx_map,
        do_condition_on_prev_tokens,
        prompt_ids,
        generation_config,
        config,
        device,
        suppress_tokens,
        timestamp_begin,
        kwargs,
    ):
        if "decoder_input_ids" in kwargs:
            decoder_input_ids = kwargs.pop("decoder_input_ids")

            return decoder_input_ids, kwargs

        cut_off_length = config.max_target_positions // 2 - 1

        decoder_input_ids = init_tokens[batch_idx_map]

        prev_start_of_text = getattr(generation_config, "prev_sot_token_id", None)
        if prev_start_of_text is None:
            if suppress_tokens is not None and len(suppress_tokens) >= 2:
                prev_start_of_text = suppress_tokens[-2]
            else:
                prev_start_of_text = None

        if any(do_condition_on_prev_tokens) and len(current_segments[0]) > 0:
            # according to https://github.com/openai/whisper/blob/e58f28804528831904c3b6f2c0e473f346223433/whisper/decoding.py#L609
            active_segments = [current_segments[i] if do_condition_on_prev_tokens[i] else None for i in batch_idx_map]

            if prompt_ids is not None and generation_config.prompt_condition_type == "all-segments":
                prev_ids = prompt_ids
            else:
                one_tensor = torch.ones((cur_bsz, 1), device=device, dtype=torch.long)
                prev_ids = prev_start_of_text * one_tensor[0] if prev_start_of_text is not None else None

            padding = "max_length" if generation_config.cache_implementation == "static" else "longest"

            prev_tokens = _pad_to_max_length(
                active_segments,
                generation_config.pad_token_id,
                device=device,
                padding_side="left",
                padding=padding,
                bos_token_tensor=prev_ids,
                cut_off_length=cut_off_length,
                skip_ending_double_timestamps=True,
                timestamp_begin=timestamp_begin,
            )
            decoder_input_ids = torch.cat([prev_tokens, decoder_input_ids], dim=-1)

            kwargs["decoder_attention_mask"] = decoder_input_ids != generation_config.pad_token_id
        elif prompt_ids is not None:
            prev_tokens = prompt_ids[None].repeat(decoder_input_ids.shape[0], 1)
            decoder_input_ids = torch.cat([prev_tokens, decoder_input_ids], dim=-1)
            # make sure `"decoder_attention_mask"` is not passed to forward
            kwargs.pop("decoder_attention_mask", None)
        else:
            # make sure `"decoder_attention_mask"` is not passed to forward
            kwargs.pop("decoder_attention_mask", None)

        return decoder_input_ids, kwargs