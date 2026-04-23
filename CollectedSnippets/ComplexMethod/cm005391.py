async def sse_gen() -> AsyncGenerator[str, None]:
            try:
                done = False
                while not done:
                    text = await queue.get()
                    batch = [text]
                    try:
                        while True:
                            batch.append(queue.get_nowait())
                    except asyncio.QueueEmpty:
                        pass

                    sse_parts: list[str] = []
                    for text in batch:
                        if text is None:
                            done = True
                            break
                        if isinstance(text, _StreamError):
                            sse_parts.append(f'data: {{"error": "{text.msg}"}}\n\n')
                            yield "".join(sse_parts)
                            return

                        sse_parts.append(self._build_chunk_sse(request_id, model_id, text=text))

                    if sse_parts:
                        yield "".join(sse_parts)

                hit_max = gen_config.max_new_tokens is not None and streamer.total_tokens >= gen_config.max_new_tokens
                finish_reason = "length" if hit_max else "stop"

                if suffix is not None:
                    yield self._build_chunk_sse(request_id, model_id, text=suffix)
                usage = CompletionUsage(
                    prompt_tokens=input_len,
                    completion_tokens=streamer.total_tokens,
                    total_tokens=input_len + streamer.total_tokens,
                )
                yield self._build_chunk_sse(request_id, model_id, finish_reason=finish_reason, usage=usage)
            except (GeneratorExit, asyncio.CancelledError):
                streamer.cancel()
                raise