async def _stream():
        emitter = AnthropicStreamEmitter()
        for line in emitter.start(message_id, model_name):
            yield line

        gen = run_gen()
        try:
            while True:
                if await request.is_disconnected():
                    cancel_event.set()
                    return
                cumulative = await asyncio.to_thread(next, gen, _sentinel)
                if cumulative is _sentinel:
                    break
                if isinstance(cumulative, dict):
                    if cumulative.get("type") == "metadata":
                        for line in emitter.feed(cumulative):
                            yield line
                    continue
                # Plain generator yields cumulative text strings
                for line in emitter.feed({"type": "content", "text": cumulative}):
                    yield line
        except Exception as e:
            logger.error("anthropic_messages stream error: %s", e)

        for line in emitter.finish("end_turn"):
            yield line