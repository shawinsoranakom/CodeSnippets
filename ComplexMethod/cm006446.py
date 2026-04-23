async def text_chunker_with_timeout(chunks, timeout=0.3):
    splitters = (".", ",", "?", "!", ";", ":", "—", "-", "(", ")", "[", "]", "}", " ")
    buffer = ""
    ait = chunks.__aiter__()
    while True:
        try:
            text = await asyncio.wait_for(ait.__anext__(), timeout=timeout)
        except asyncio.TimeoutError:
            if buffer:
                yield buffer + " "
                buffer = ""
            continue
        except StopAsyncIteration:
            break
        if text is None:
            if buffer:
                yield buffer + " "
            break
        if buffer and buffer[-1] in splitters:
            yield buffer + " "
            buffer = text
        elif text and text[0] in splitters:
            yield buffer + text[0] + " "
            buffer = text[1:]
        else:
            buffer += text
    if buffer:
        yield buffer + " "