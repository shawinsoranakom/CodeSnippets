def _decode_asr(tokenizer, model_outputs, *, return_timestamps, return_language, time_precision, segment_size=1500):
    """
    Internal method meant to only be used by asr pipeline. Handles all the little quirks specific to whisper to handle
    the various options not allowed in other seq2seq models
    """

    # =========== Overview ============
    # - iterate over all outputs
    # - all tokens within output
    # - Each token can be
    #   - language token
    #   - special token
    #   - timestamp token
    #   - text token
    # - We accumulate the text tokens.
    # - We split on end timestamps
    # - Lots of complexity comes from stride and timestamps

    last_language = None

    def new_chunk():
        return {"language": last_language, "timestamp": [None, None], "text": ""}

    # Welcome to the state machine !
    chunks = []
    chunk = new_chunk()
    time_offset = 0.0
    timestamp_begin = tokenizer.convert_tokens_to_ids("<|notimestamps|>") + 1
    previous_tokens = []
    previous_token_timestamps = []
    skip = False
    right_stride_start = None

    all_special_ids = set(tokenizer.all_special_ids)
    prompt_token_id = tokenizer.convert_tokens_to_ids("<|startofprev|>")
    decoder_start_token_id = tokenizer.convert_tokens_to_ids("<|startoftranscript|>")
    # - iterate over all outputs
    for chunk_id, output in enumerate(model_outputs):
        # We can drop everything to Python list, it's going to make
        # our lives easier
        token_ids = output["tokens"][0].tolist()
        # (possibly) remove the prompt from the token ids
        token_ids = tokenizer._strip_prompt(token_ids, prompt_token_id, decoder_start_token_id)
        if return_timestamps == "word":
            token_timestamps = output["token_timestamps"][0].tolist()

        # Those keep track of timestamps within strides
        # Which need to be skipped and resolve all tokens in a single
        # chunk.
        last_timestamp = None
        first_timestamp = timestamp_begin

        # long form generation: we need to handle the case where the call to generate returns concatenated segments,
        # with underlying multiple calls to generate
        cur_max_timestamp = 0.0
        prev_segments_len = 0.0
        penultimate_timestamp = 0.0

        if "stride" in output:
            chunk_len, stride_left, stride_right = output["stride"]
            # Offset the timings to account for the other `model_outputs`.
            time_offset -= stride_left
            right_stride_start = chunk_len - stride_right

            # Keeping track of timestamps within strides
            # We're going to NOT split on those, and delay until we're
            # out of BOTH stride. Otherwise lots of issues occur and
            # corner cases
            if stride_left:
                first_timestamp = stride_left / time_precision + timestamp_begin
            if stride_right:
                for token in reversed(token_ids):
                    if token >= timestamp_begin:
                        # There can be several token in the right stride
                        # But the last one is ALWAYS going to be skipped
                        if (
                            last_timestamp is not None
                            and (token - timestamp_begin) * time_precision < right_stride_start
                        ):
                            break
                        last_timestamp = token

        current_tokens = []
        current_token_timestamps = []

        # - all tokens within output
        for i, token in enumerate(token_ids):
            # 4 possible states for each token
            # - 1/ Language code
            # - 2/ all other special tokens (which we ignore)
            # - 3/ Timestamp
            # - 4/ Regular text
            if token in all_special_ids:
                # Either language code or other
                text = tokenizer.decode([token])
                # Removing outer shell <|XX|>
                text = text[2:-2]
                language = LANGUAGES.get(text)
                if language is not None:
                    # 1/ Indeed some language
                    # TODO Handle when language is different from the previous
                    # one, and we cannot use timestamped tokens to create chunks
                    if last_language and language != last_language and not return_timestamps:
                        previous_tokens.append(current_tokens)
                        resolved_tokens = _find_longest_common_sequence(previous_tokens)
                        resolved_text = tokenizer.decode(resolved_tokens)
                        chunk["text"] = resolved_text
                        chunks.append(chunk)

                        # Flush all our temporary context
                        previous_tokens = []
                        current_tokens = []
                        chunk = new_chunk()
                    chunk["language"] = language
                    last_language = language
                else:
                    # 2/ This is a regular special token, ignoring it
                    pass
            elif token >= timestamp_begin:
                # 3/ Timestamp token

                timestamp = float((token - timestamp_begin) * time_precision)
                if timestamp < cur_max_timestamp:
                    # next segment has started
                    last_was_single_ending = i >= 2 and not (
                        token_ids[i - 1] >= timestamp_begin and token_ids[i - 2] >= timestamp_begin
                    )
                    if last_was_single_ending:
                        prev_segments_len += time_precision * segment_size
                    else:
                        cur_max_timestamp = penultimate_timestamp
                        prev_segments_len += penultimate_timestamp

                penultimate_timestamp = cur_max_timestamp
                cur_max_timestamp = timestamp

                time = (token - timestamp_begin) * time_precision + time_offset + prev_segments_len

                time = round(time, 2)
                if last_timestamp and token >= last_timestamp:
                    # Whisper outputted a timestamp token, but it falls within
                    # our stride, so we're going to skip it for the time being
                    # and resolve this later
                    # Skip is necessary because timestamp tokens always come
                    # by pair, so we need to skip the next one too (which would mark the start of another chunk).
                    skip = True
                elif skip or (previous_tokens and token < first_timestamp):
                    skip = False
                elif chunk["timestamp"][0] is None:
                    chunk["timestamp"][0] = time
                else:
                    # This is the end of the timestamp chunk
                    if time == chunk["timestamp"][0]:
                        # This is a bug in timestamp token output
                        # where we're taking the duplicate token
                        # as a stop where it should be a start.
                        # This is an issue in the underlying model output
                        # Let's just skip it so it becomes de-factor
                        # a start again
                        pass
                    else:
                        chunk["timestamp"][1] = time
                        # Handling merges.
                        previous_tokens.append(current_tokens)
                        if return_timestamps == "word":
                            previous_token_timestamps.append(current_token_timestamps)
                        resolved_tokens, resolved_token_timestamps = _find_longest_common_sequence(
                            previous_tokens, previous_token_timestamps
                        )
                        resolved_text = tokenizer.decode(resolved_tokens)
                        chunk["text"] = resolved_text
                        if return_timestamps == "word":
                            chunk["words"] = _collate_word_timestamps(
                                tokenizer, resolved_tokens, resolved_token_timestamps, last_language, return_language
                            )
                        chunks.append(chunk)

                        # Flush all our temporary context
                        previous_tokens = []
                        current_tokens = []
                        previous_token_timestamps = []
                        current_token_timestamps = []
                        chunk = new_chunk()
            else:
                # 4/ Regular token
                # We just append to the list of all tokens so we can handle
                # merges later and decode into text.
                current_tokens.append(token)
                if return_timestamps == "word":
                    if i == 0:
                        start_time = round(0.0 + time_offset, 2)
                    else:
                        start_time = round(token_timestamps[i - 1] + time_offset, 2)
                    end_time = round(token_timestamps[i] + time_offset, 2)
                    current_token_timestamps.append((start_time, end_time))

        if "stride" in output:
            time_offset += chunk_len - stride_right

        # Leftover tokens
        if current_tokens:
            previous_tokens.append(current_tokens)
            if return_timestamps == "word":
                previous_token_timestamps.append(current_token_timestamps)
        elif not (any(p for p in previous_tokens)):
            chunk = new_chunk()
            previous_tokens = []
            current_tokens = []
            previous_token_timestamps = []
            current_token_timestamps = []

    if previous_tokens:
        if return_timestamps:
            logger.warning(
                "Whisper did not predict an ending timestamp, which can happen if audio is cut off in the middle of a word. "
                "Also make sure WhisperTimeStampLogitsProcessor was used during generation."
            )
        # Happens when we don't use timestamps
        resolved_tokens, resolved_token_timestamps = _find_longest_common_sequence(
            previous_tokens, previous_token_timestamps
        )
        resolved_text = tokenizer.decode(resolved_tokens)
        chunk["text"] = resolved_text
        if return_timestamps == "word":
            chunk["words"] = _collate_word_timestamps(
                tokenizer, resolved_tokens, resolved_token_timestamps, last_language, return_language
            )
        chunks.append(chunk)

    # Preparing and cleaning up the pipeline output
    full_text = "".join(chunk["text"] for chunk in chunks)
    if return_timestamps or return_language:
        for chunk in chunks:
            if not return_timestamps:
                chunk.pop("timestamp")
            else:
                chunk["timestamp"] = tuple(chunk["timestamp"])
            if not return_language:
                chunk.pop("language")

        if return_timestamps == "word":
            new_chunks = []
            for chunk in chunks:
                new_chunks.extend(chunk["words"])
            optional = {"chunks": new_chunks}
        else:
            optional = {"chunks": chunks}
    else:
        optional = {}
    return full_text, optional