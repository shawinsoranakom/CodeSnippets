def _retrieve_segment(
        seek_sequence,
        seek_outputs,
        time_offset,
        timestamp_begin,
        seek_num_frames,
        time_precision,
        time_precision_features,
        input_stride,
        prev_idx,
        idx,
        return_token_timestamps,
        decoder_input_ids,
    ):
        # find the predicted "end of segment" predictions of Whisper
        # "end of segment" predictions occur whenever Whisper predicts a timestamp token
        timestamp_tokens: torch.Tensor = seek_sequence.ge(timestamp_begin)
        single_timestamp_ending = timestamp_tokens[-2:].tolist() == [False, True]
        timestamp_segment_indices = torch.where(timestamp_tokens[:-1] & timestamp_tokens[1:])[0]
        timestamp_segment_indices.add_(1)
        token_timestamps = seek_outputs[idx]["token_timestamps"] if return_token_timestamps else []
        idx_offset = decoder_input_ids.shape[-1]
        device = seek_sequence.device

        # If whisper predicted a "end of segment" via a timestep token, let's go ever each
        # "end of segment" prediction and slice the decoding into segments accordingly
        if len(timestamp_segment_indices) > 0:
            # if the output contains two consecutive timestamp tokens
            slices = timestamp_segment_indices.tolist()
            segments = []
            if single_timestamp_ending:
                slices.append(len(seek_sequence))
            else:
                # we want to include the last timestamp token in the last segment to know it was no single ending
                slices[-1] += 1

            last_slice = 0
            # Add each segment to list of all segments
            for i, current_slice in enumerate(slices):
                is_last_slice = i == len(slices) - 1
                sliced_tokens = seek_sequence[last_slice:current_slice]
                start_timestamp_pos = sliced_tokens[0] - timestamp_begin
                idx_sliced_tokens = -1 if not is_last_slice or single_timestamp_ending else -2
                end_timestamp_pos = sliced_tokens[idx_sliced_tokens] - timestamp_begin
                segments.append(
                    {
                        "start": time_offset[prev_idx]
                        + start_timestamp_pos.to(torch.float32 if device.type == "mps" else torch.float64)
                        * time_precision,
                        "end": time_offset[prev_idx]
                        + end_timestamp_pos.to(torch.float32 if device.type == "mps" else torch.float64)
                        * time_precision,
                        "tokens": sliced_tokens,
                        "idxs": (idx_offset + last_slice, idx_offset + current_slice),
                        "result": seek_outputs[idx],
                    }
                )
                if return_token_timestamps:
                    segments[-1]["token_timestamps"] = (
                        token_timestamps[idx_offset + last_slice : idx_offset + current_slice] + time_offset[prev_idx]
                    )
                last_slice = current_slice

            if single_timestamp_ending:
                # single timestamp at the end means no speech after the last timestamp.
                segment_offset = seek_num_frames[prev_idx]
            else:
                # otherwise, ignore the unfinished segment and seek to the last timestamp
                # here we throw away all predictions after the last predicted "end of segment"
                # since we are cutting right in the middle of an audio
                last_timestamp_pos = seek_sequence[last_slice - 2].item() - timestamp_begin
                segment_offset = last_timestamp_pos * input_stride
        else:
            # If whisper does not predict any "end of segment" token, then
            # the whole decoding is considered a segment and we add it to the list of segments
            timestamps = seek_sequence[timestamp_tokens.nonzero().flatten()]
            last_timestamp_pos = int(seek_num_frames[prev_idx] * time_precision_features / time_precision)
            if timestamps.numel() > 0 and timestamps[-1] != timestamp_begin:
                # no consecutive timestamps but it has a timestamp; use the last one.
                last_timestamp_pos = (timestamps[-1] - timestamp_begin).to(
                    torch.float32 if device.type == "mps" else torch.float64
                )
            segments = [
                {
                    "start": time_offset[prev_idx],
                    "end": time_offset[prev_idx] + last_timestamp_pos * time_precision,
                    "tokens": seek_sequence,
                    "idxs": (idx_offset, idx_offset + len(seek_sequence)),
                    "result": seek_outputs[idx],
                }
            ]
            if return_token_timestamps:
                segments[-1]["token_timestamps"] = (
                    token_timestamps[idx_offset : idx_offset + len(seek_sequence)] + time_offset[prev_idx]
                )
            segment_offset = seek_num_frames[prev_idx]

        return segments, segment_offset