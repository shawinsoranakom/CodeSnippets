async def _stream():
        emitter = AnthropicPassthroughEmitter()
        for line in emitter.start(message_id, model_name):
            yield line

        # Manage the httpx client, response, AND the aiter_lines() async
        # generator MANUALLY — no `async with`, no anonymous iterator.
        #
        # On Python 3.13 + httpcore 1.0.x, `async for raw_line in
        # resp.aiter_lines():` creates an anonymous async generator. When
        # the loop exits via `break` (or the generator is orphaned when a
        # client disconnects mid-stream), Python's `async for` protocol
        # does NOT auto-close the iterator the way a sync `for` loop
        # would. The iterator remains reachable only from the current
        # coroutine frame; once `_stream()` returns, the frame is GC'd
        # and the iterator becomes unreachable. Python's asyncgen
        # finalizer hook then runs its aclose() on a LATER GC pass in a
        # DIFFERENT asyncio task, where httpcore's
        # `HTTP11ConnectionByteStream.aclose()` enters
        # `anyio.CancelScope.__exit__` with a mismatched task and prints
        # `RuntimeError: Attempted to exit cancel scope in a different
        # task` / `RuntimeError: async generator ignored GeneratorExit`
        # as "Exception ignored in:" unraisable warnings.
        #
        # The fix: save `resp.aiter_lines()` as `lines_iter`, and in the
        # finally block explicitly `await lines_iter.aclose()` BEFORE
        # `resp.aclose()` / `client.aclose()`. This closes the iterator
        # inside our own task's event loop, so the internal httpcore
        # byte-stream is cleaned up before Python's asyncgen finalizer
        # has anything orphaned to finalize. Each aclose is wrapped in
        # `try: ... except Exception: pass` so anyio cleanup noise from
        # nested aclose paths can't bubble out.
        client = httpx.AsyncClient(timeout = 600)
        resp = None
        lines_iter = None
        try:
            req = client.build_request("POST", target_url, json = body)
            resp = await client.send(req, stream = True)

            lines_iter = resp.aiter_lines()
            async for raw_line in lines_iter:
                if await request.is_disconnected():
                    cancel_event.set()
                    break
                if not raw_line or not raw_line.startswith("data: "):
                    continue
                data_str = raw_line[6:]
                if data_str.strip() == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                for line in emitter.feed_chunk(chunk):
                    yield line
        except Exception as e:
            logger.error("anthropic_messages passthrough stream error: %s", e)
        finally:
            if lines_iter is not None:
                try:
                    await lines_iter.aclose()
                except Exception:
                    pass
            if resp is not None:
                try:
                    await resp.aclose()
                except Exception:
                    pass
            try:
                await client.aclose()
            except Exception:
                pass

        for line in emitter.finish():
            yield line