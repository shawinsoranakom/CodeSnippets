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
                event = await asyncio.to_thread(next, gen, _sentinel)
                if event is _sentinel:
                    break
                # Strip leaked tool-call XML from content events
                if event.get("type") == "content":
                    event = dict(event)
                    event["text"] = _TOOL_XML_RE.sub("", event["text"])
                for line in emitter.feed(event):
                    yield line
        except Exception as e:
            logger.error("anthropic_messages stream error: %s", e)

        for line in emitter.finish("end_turn"):
            yield line