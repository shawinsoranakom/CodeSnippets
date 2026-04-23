def add_ai_message_chunks(
    left: AIMessageChunk, *others: AIMessageChunk
) -> AIMessageChunk:
    """Add multiple `AIMessageChunk`s together.

    Args:
        left: The first `AIMessageChunk`.
        *others: Other `AIMessageChunk`s to add.

    Returns:
        The resulting `AIMessageChunk`.

    """
    content = merge_content(left.content, *(o.content for o in others))
    additional_kwargs = merge_dicts(
        left.additional_kwargs, *(o.additional_kwargs for o in others)
    )
    response_metadata = merge_dicts(
        left.response_metadata, *(o.response_metadata for o in others)
    )

    # Merge tool call chunks
    if raw_tool_calls := merge_lists(
        left.tool_call_chunks, *(o.tool_call_chunks for o in others)
    ):
        tool_call_chunks = [
            create_tool_call_chunk(
                name=rtc.get("name"),
                args=rtc.get("args"),
                index=rtc.get("index"),
                id=rtc.get("id"),
            )
            for rtc in raw_tool_calls
        ]
    else:
        tool_call_chunks = []

    # Token usage
    if left.usage_metadata or any(o.usage_metadata is not None for o in others):
        usage_metadata: UsageMetadata | None = left.usage_metadata
        for other in others:
            usage_metadata = add_usage(usage_metadata, other.usage_metadata)
    else:
        usage_metadata = None

    # Ranks are defined by the order of preference. Higher is better:
    # 2. Provider-assigned IDs (non lc_* and non lc_run-*)
    # 1. lc_run-* IDs
    # 0. lc_* and other remaining IDs
    best_rank = -1
    chunk_id = None
    candidates = itertools.chain([left.id], (o.id for o in others))

    for id_ in candidates:
        if not id_:
            continue

        if not id_.startswith(LC_ID_PREFIX) and not id_.startswith(LC_AUTO_PREFIX):
            chunk_id = id_
            # Highest rank, return instantly
            break

        rank = 1 if id_.startswith(LC_ID_PREFIX) else 0

        if rank > best_rank:
            best_rank = rank
            chunk_id = id_

    chunk_position: Literal["last"] | None = (
        "last" if any(x.chunk_position == "last" for x in [left, *others]) else None
    )

    return left.__class__(
        content=content,
        additional_kwargs=additional_kwargs,
        tool_call_chunks=tool_call_chunks,
        response_metadata=response_metadata,
        usage_metadata=usage_metadata,
        id=chunk_id,
        chunk_position=chunk_position,
    )