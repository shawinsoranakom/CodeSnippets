def _find_timestamp_sequence(sequences, tokenizer, feature_extractor, max_source_positions):
    """
    Old processing function used in the ASR pipeline.

    Computes the final sequences by merging the end of the nth sequence with the beginning of the n+1th sequence. Since
    `WhisperForConditionalGeneration` produces the timestamps pairwise, we filter the consecutive timestamps and only
    iterate over them. We keep track of the `time` which indicates the actual starting time of the chunk that is
    processed. We need to make sure to offset the timestamps tokens by the `time` in order for the tokenizer to
    properly compute the final `offset`.
    """
    # index of the first timestamp token
    timestamp_begin = tokenizer.convert_tokens_to_ids("<|notimestamps|>") + 1
    items = []
    # approximation of the token to time ratio : ~0.2seconds
    time_precision = feature_extractor.chunk_length / max_source_positions
    time = 0
    for seq_idx, item in enumerate(sequences):
        sequence, stride = item
        if isinstance(sequence, list):
            sequence = np.array(sequence)
        chunk_len, stride_left, stride_right = stride
        sequence = sequence.squeeze(0)
        # get rid of the `forced_decoder_idx` that are use to parametrize the generation
        begin_idx = np.where(sequence == timestamp_begin)[0][0] if timestamp_begin in sequence else 0
        sequence = sequence[begin_idx:]

        timestamp_tokens = sequence >= timestamp_begin
        if seq_idx != 0 and sum(timestamp_tokens) > 0:
            consecutive = np.where(timestamp_tokens[:-1] & timestamp_tokens[1:])[0] + 1
            last_timestamp = np.where(timestamp_tokens)[0][-1]
            consecutive = np.append(consecutive, last_timestamp) if last_timestamp not in consecutive else consecutive
            time -= stride_left + stride_right
            offset = int((time / feature_extractor.sampling_rate) / time_precision)
            overlap_time = int((stride_left / feature_extractor.sampling_rate) / time_precision)
            # relevant timestamps are in the overlapping part
            relevant_timestamp = np.where(sequence[consecutive] >= timestamp_begin + overlap_time)[0]
            if relevant_timestamp.shape[0] > 0:
                relevant_timestamp = (
                    consecutive[relevant_timestamp[0] - 1] if relevant_timestamp[0] > 0 else consecutive[0]
                )
                # if a big stride is used, we need to check some of the previous items for the best overlap
                best_match = 0
                sliced_sequence = []
                for idx, previous_sequence in enumerate(reversed(items)):
                    previous_tokens = previous_sequence[1:-1]
                    if previous_sequence[0] < (timestamp_begin + offset - overlap_time) and idx != 0:
                        break  # the previous sequence is too far in the past
                    if len(previous_tokens) > 0:
                        # find the longest common sequence between the overlapping parts
                        index_left, index_right, match_length = _fast_find_longest_common_sequence(
                            sequence[1:relevant_timestamp], previous_tokens
                        )
                        # don't do anything if only 1 token was matched
                        if match_length > 1 and match_length > best_match:
                            best_match = match_length
                            best_idx = idx
                            end_of_curr_sequence_idx = (
                                np.where(sequence[index_left + 1 :] >= timestamp_begin)[0][0] + 1
                            )
                            end_of_curr_sequence_idx = end_of_curr_sequence_idx + 1 + index_left
                            # if all the tokens are matched, suffix
                            if index_left == 0 and match_length == len(previous_tokens):
                                sliced_sequence = np.insert(
                                    sequence[index_left + 1 : end_of_curr_sequence_idx], 0, previous_sequence[0]
                                )
                                sliced_sequence[-1] = previous_sequence[-1]
                            # if part of the previous sequence is not taken
                            elif index_left >= 0:
                                sliced_sequence = sequence[index_left + 1 : end_of_curr_sequence_idx]
                                # let's insert the missing part of the previous sequence
                                previous_slice = (
                                    previous_sequence[: index_right + 1] if index_right > 0 else [previous_sequence[0]]
                                )
                                sliced_sequence = np.insert(sliced_sequence, 0, previous_slice)
                                sliced_sequence[-1] += offset

                if len(sliced_sequence) > 0:
                    items[len(items) - best_idx - 1] = sliced_sequence
                    items = items[: len(items) - best_idx]
                    sequence = sequence[end_of_curr_sequence_idx:]

        # sequence might have changed
        timestamp_tokens = sequence >= timestamp_begin
        consecutive = np.where(timestamp_tokens[:-1] & timestamp_tokens[1:])[0] + 1
        if sum(timestamp_tokens) > 0:
            last_timestamp = np.where(timestamp_tokens)[0][-1]
            consecutive = (
                np.append(consecutive, last_timestamp + 1) if last_timestamp not in consecutive else consecutive
            )

        if len(consecutive) > 0:
            last_slice = 0
            for current_slice in consecutive:
                actual_offset = items[-1][-1] if seq_idx != 0 or last_slice != 0 else sequence[0]
                sliced_tokens = sequence[last_slice:current_slice]
                duration = sliced_tokens[-1] - sliced_tokens[0]
                sliced_tokens[0] = actual_offset
                sliced_tokens[-1] = actual_offset + duration
                items.append(sliced_tokens)
                last_slice = current_slice

        time += chunk_len
    result = []
    for i in range(len(items)):
        result += items[i].tolist()
    return result