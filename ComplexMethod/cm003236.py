def _pad_to_max_length(
    current_segments,
    pad_token_id,
    device,
    padding_side="right",
    padding="longest",
    bos_token_tensor=None,
    cut_off_length=None,
    return_token_timestamps=False,
    force_unique_generate_call=False,
    skip_ending_double_timestamps=False,
    timestamp_begin=None,
):
    """
    skip_ending_double_timestamps: when the segment ended with two timestamp tokens, whether to ignore the last timestamp token
    see https://github.com/huggingface/transformers/pull/35750

    _pad_to_max_length is used in different contexts:
    1. At the end of generation: we need to keep both ending timestamp tokens in the segment (see https://github.com/huggingface/transformers/pull/34537).
    2. In the middle of generation, e.g. when condition_on_prev_tokens=True and we want to use the last generated tokens as decoder_input_ids:
       we must skip one of the double ending timestamp tokens (see https://github.com/huggingface/transformers/pull/35750).
    """
    max_total_length = 0
    sequences = []
    token_timestamps_list = []

    if padding_side not in ["right", "left"]:
        raise ValueError(f"`padding_side` must be either 'right' or 'left', not {padding_side}")

    if padding not in ["longest", "max_length"]:
        raise ValueError(f"`padding` must be either 'longest' or 'max_length', not {padding}")
    elif padding == "max_length" and cut_off_length is None:
        raise ValueError("`cut_off_length` must be specified when `padding='max_length'`")

    if force_unique_generate_call:
        sequences_list = []
        timestamps_list = []
        for segments in current_segments:
            result = segments[0]["result"]
            sequences_list.append(result if isinstance(result, torch.Tensor) else result["sequences"])
            if return_token_timestamps:
                timestamps_list.append(result["token_timestamps"])

        sequences = torch.stack(sequences_list, dim=0)
        if return_token_timestamps:
            token_timestamps = torch.stack(timestamps_list, dim=0)
            return sequences, token_timestamps
        return sequences

    for current_segment_list in current_segments:
        if current_segment_list is not None and len([d["tokens"] for d in current_segment_list]) > 0:
            sequences_list = []
            for d in current_segment_list:
                if skip_ending_double_timestamps and len(d["tokens"]) > 2 and d["tokens"][-2] >= timestamp_begin:
                    # the segment finishes with two timestamp tokens
                    # we need to ignore the last timestamp token
                    # see https://github.com/huggingface/transformers/pull/34537
                    sequences_list.append(d["tokens"][:-1])
                else:
                    sequences_list.append(d["tokens"])
            sequence = torch.cat(sequences_list, dim=-1)

            if return_token_timestamps:
                token_timestamps = torch.cat(
                    [d["result"]["token_timestamps"][d["idxs"][0] : d["idxs"][1]] for d in current_segment_list],
                    dim=-1,
                )

            if cut_off_length is not None:
                sequence = sequence[-cut_off_length:]
                if return_token_timestamps:
                    token_timestamps = token_timestamps[-cut_off_length:]

            if bos_token_tensor is not None:
                sequence = torch.cat([bos_token_tensor, sequence])
                if return_token_timestamps:
                    token_timestamps = torch.cat(
                        [torch.ones_like(bos_token_tensor, device=device) * 0.0, token_timestamps]
                    )
            sequences.append(sequence)
            if return_token_timestamps:
                token_timestamps_list.append(token_timestamps)
            max_total_length = max(max_total_length, len(sequences[-1]))
        elif bos_token_tensor is not None:
            sequences.append(bos_token_tensor)
            if return_token_timestamps:
                token_timestamps_list.append(torch.ones_like(bos_token_tensor, device=device) * 0.0)
        else:
            sequences.append(torch.tensor([], device=device))
            if return_token_timestamps:
                token_timestamps_list.append(torch.tensor([], device=device))

    max_total_length = cut_off_length + 1 if padding == "max_length" else max_total_length
    for i in range(len(current_segments)):
        pad_length = max_total_length - len(sequences[i])
        pad = (0, pad_length) if padding_side == "right" else (pad_length, 0)

        sequences[i] = F.pad(sequences[i], pad=pad, value=pad_token_id)
        if return_token_timestamps:
            token_timestamps_list[i] = F.pad(
                token_timestamps_list[i],
                pad=pad,
                value=token_timestamps_list[i][-1] if len(token_timestamps_list[i]) > 0 else 0.0,
            )

    sequences = torch.stack(sequences, dim=0)

    if return_token_timestamps:
        token_timestamps = torch.stack(token_timestamps_list, dim=0)
        return sequences, token_timestamps
    else:
        return sequences