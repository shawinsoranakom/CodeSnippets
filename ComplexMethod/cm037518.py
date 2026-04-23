def recompute_mrope_positions(
    input_ids: torch.LongTensor,
    multimodal_positions: list[torch.Tensor],
    mrope_positions: torch.LongTensor,
    num_computed_tokens: int,
    vision_start_token_id: int,
    image_token_id: int,
    video_token_id: int,
) -> tuple[torch.LongTensor, int]:
    """
    Update part of input mrope positions.
    Original mrope_positions are computed incorrectly, so once we prune media
    tokens we should reflect this in the mrope positions for the LLM.

    This method supports chunked prefill approach where
    multimodal_embeddings are passed to LLM in chunks, so input
    multimodal_embeddings may contain zero, some or even some part of all
    multimodal_embeddings for a given prompt.

    Each multimodal_positions has 4 or 5 extra channels
    (first 3 channels correspond to the original 3 mrope positions;
    remaining channels vary by model — see below). Provided multimodal_positions
    do not reflect location of media position in sequence - they are computed
    like the media is in the 0-th position in the sequence.

    Method works as follows: it recomputes mrope_positions starting from the
    `num_computed_tokens` for `total_len_of_multimodal_embeddings` and then
    shifts all text tokens that goes after total_len_of_multimodal_embeddings.

    It also handles case when multimodal_embeddings is partial
    (e.g. one media is split into two prefill stages)

    Args:
        input_ids: (N,) All input tokens of the prompt (entire sequence).
        multimodal_positions: List of mrope positions for each media.
            If a given element is of shape (4, N), it is assumed to only describe
            positions for video / image embeddings. This is the case of e.g. Qwen2.5 VL,
            where each multimodal input is a contiguous chunk of embeddings.
            The expected channels are [t, h, w, max_width].
            If it is of shape (5, N), it is assumed to possibly describe positions for
            both video / image embeddings, as well as text embeddings. This is the case
            of e.g. Qwen3 VL, where each video inputs are comprised of individual
            frames' embeddings, interleaved with embeddings for timestamp tokens,
            and vision start / end tokens. The expected channels are
            [t, h, w, is_vision_start, is_vision].
        mrope_positions: Existing mrope positions (4, N) for entire sequence.
        num_computed_tokens: A number of computed tokens so far.
        vision_start_token_id: Token indicating start of vision media.
        image_token_id: Image token id
        video_token_id: Video token id

    Returns:
        Tuple of (mrope_positions, mrope_position_delta).
    """

    # Tensors
    positions: torch.LongTensor = typing.cast(
        torch.LongTensor, mrope_positions.clone()
    )  # (3, N)
    N = input_ids.numel()

    image_mask = input_ids.eq(image_token_id)
    video_mask = input_ids.eq(video_token_id)
    media_mask = image_mask | video_mask
    text_mask = ~media_mask

    # Early exit: no media in this chunk
    if len(multimodal_positions) == 0:
        delta = int((positions.max().item() + 1) - N) if positions.numel() else -N
        return positions, delta

    total_mm_tokens = torch.count_nonzero(media_mask)
    seen_mm_tokens = torch.count_nonzero(media_mask[:num_computed_tokens])

    # Early exit: we've updated positions for all media tokens
    # (and consequently - for all remaining text tokens)
    if seen_mm_tokens == total_mm_tokens:
        delta = int((positions.max().item() + 1) - N) if positions.numel() else -N
        return positions, delta

    vision_start_indices = (input_ids == vision_start_token_id).nonzero(as_tuple=True)[
        0
    ]

    for mm_pos in multimodal_positions:
        # Each mm_pos can be a complete embedding for single media
        # or it can be a part of a single media (due to chunked prefill)

        # Cases to cover
        # - Current prefill chunk has no vision start indexes at all
        # - Vision start token appeared in previous prefill round
        # - Regular case
        has_video_tokens = False
        num_timestamp_tokens = 0
        if mm_pos.shape[0] == 5 and mm_pos.shape[1] > 0:
            # mm_pos[4, :] indicates which positions are for video embeddings.
            # If there are no video embeddings, skip timestamp adjustment.
            has_video_tokens = torch.any(mm_pos[4, :]).item()
            if has_video_tokens:
                # Channel 3 flags VISION_START tokens.  Timestamp tokens
                # precede the first VISION_START, so its index gives us the
                # exact timestamp count.  This is robust even when early
                # frames have all their video tokens pruned (which would
                # push argmax(channel 4) far into a later frame).
                first_vs = (mm_pos[3, :] == 1).nonzero(as_tuple=True)[0]
                num_timestamp_tokens = first_vs[0].item() if len(first_vs) > 0 else 0

        seen_vision_start_indices = vision_start_indices[
            vision_start_indices < num_computed_tokens
        ]

        if len(seen_vision_start_indices):
            # If we have encountered some vision start indexes,
            # then we should check the condition:
            # | --- prefill 1 ------| ---- prefill 2 ----- |
            # | TTTTTTTTTSVVVVVVVVVV|VVVVVVTTTTTTTTTTTTTTTT|
            last_vision_start_token = seen_vision_start_indices[-1]
            seem_mm_tokens_before_last_vision_start = torch.count_nonzero(
                media_mask[:last_vision_start_token]
            )
            in_the_middle_of_media = (
                seen_mm_tokens > seem_mm_tokens_before_last_vision_start
            )
            # For Qwen3 VL, we can be inside a media segment even before any
            # video tokens appear (timestamp tokens are text). If we've passed
            # the last vision_start token but haven't reached the first video
            # embedding, treat this as "in the middle of media".
            if (
                not in_the_middle_of_media
                and has_video_tokens
                and num_computed_tokens > last_vision_start_token
                and num_computed_tokens
                <= last_vision_start_token + num_timestamp_tokens + 1
            ):
                in_the_middle_of_media = True

            if in_the_middle_of_media:
                mm_embeddings_seen = (
                    seen_mm_tokens - seem_mm_tokens_before_last_vision_start
                )
                global_mm_start = last_vision_start_token
            else:
                # We have completed previous mm_embedding part and
                # ready to start a new one
                next_vision_start_token = vision_start_indices[
                    vision_start_indices >= num_computed_tokens
                ][0]
                mm_embeddings_seen = 0
                global_mm_start = next_vision_start_token

        else:
            # If there were no vision start indexes so far,
            # let's find first vision start index
            next_vision_start_token = vision_start_indices[
                vision_start_indices >= num_computed_tokens
            ][0]

            mm_embeddings_seen = 0
            global_mm_start = next_vision_start_token

        # For Qwen3 VL, mm_pos includes timestamp tokens before vision_start
        # when starting a new media. Adjust global_mm_start to point to where
        # the sequence actually begins (before timestamp tokens).
        adjusted_for_timestamps = False
        if mm_pos.shape[0] == 5 and mm_embeddings_seen == 0 and has_video_tokens:
            # NOTE: -1 is because there is a vision start token right after
            # timestamp tokens before any video embeddings appear.

            # Adjust global_mm_start to point to the first timestamp token
            # instead of the vision_start token.
            global_mm_start -= num_timestamp_tokens
            adjusted_for_timestamps = True

        # Offset calculation depends on whether we adjusted for timestamp tokens
        if adjusted_for_timestamps:
            # Start from position before the first timestamp token
            base = positions[-1, global_mm_start - 1] + 1
            local_start = global_mm_start + mm_embeddings_seen
        else:
            # Original logic: start after vision_start_token
            base = positions[-1, global_mm_start] + 1
            local_start = global_mm_start + 1 + mm_embeddings_seen

        local_end = local_start + mm_pos.shape[1]
        positions[:, local_start:local_end] = mm_pos[0:3] + base

        # For Qwen3 VL (5-channel), use the maximum position reached across
        # all tokens (both video and text) in all dimensions (t, h, w).
        # For Qwen2.5 VL (4-channel), mm_pos[3, 0] is the max width.
        if mm_pos.shape[0] == 5:
            offset = mm_pos[0:3, :].max() + base + 1
        else:
            offset = mm_pos[3, 0] + base

        text_pos_sum = torch.cumsum(text_mask[local_end:].long(), dim=0)

        positions[:, local_end:N] = text_pos_sum + offset - 1

        # Include distance to the next vision start token
        num_computed_tokens += mm_pos.shape[1]

    mrope_positions_delta = (positions.max() + 1 - N).item()
    return positions, mrope_positions_delta