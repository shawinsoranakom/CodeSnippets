async def _stream_with_think_delta(stream_iter, min_tokens: int = 16):
    state = _ThinkStreamState()
    async for chunk in stream_iter:
        if not chunk:
            continue
        if chunk.startswith(state.last_model_full):
            new_part = chunk[len(state.last_model_full):]
            state.last_model_full = chunk
        else:
            new_part = chunk
            state.last_model_full += chunk
        if not new_part:
            continue
        state.full_text += new_part
        delta = _next_think_delta(state)
        if not delta:
            continue
        if delta in ("<think>", "</think>"):
            if delta == "<think>" and state.in_think:
                continue
            if delta == "</think>" and not state.in_think:
                continue
            if state.buffer:
                yield ("text", state.buffer, state)
                state.buffer = ""
            state.in_think = delta == "<think>"
            yield ("marker", delta, state)
            continue
        state.buffer += delta
        if num_tokens_from_string(state.buffer) < min_tokens:
            continue
        yield ("text", state.buffer, state)
        state.buffer = ""

    if state.buffer:
        yield ("text", state.buffer, state)
        state.buffer = ""
    if state.endswith_think:
        yield ("marker", "</think>", state)