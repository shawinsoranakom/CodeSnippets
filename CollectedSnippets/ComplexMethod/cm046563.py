async def _stream():
        # Same httpx lifecycle pattern as _anthropic_passthrough_stream:
        # avoid `async with` on the client/response AND explicitly save
        # resp.aiter_lines() so we can close it ourselves in the finally
        # block. See the long comment there for the full rationale on
        # why the anonymous `async for raw_line in resp.aiter_lines():`
        # pattern leaks an unclosed async generator that Python's
        # asyncgen GC hook then finalizes in a different asyncio task,
        # producing "Exception ignored in:" / "async generator ignored
        # GeneratorExit" / anyio cancel-scope traces on Python 3.13 +
        # httpcore 1.0.x.
        lines_iter = None
        try:
            lines_iter = resp.aiter_lines()
            async for raw_line in lines_iter:
                if await request.is_disconnected():
                    cancel_event.set()
                    break
                if not raw_line:
                    continue
                if not raw_line.startswith("data: "):
                    continue
                # Relay the llama-server SSE chunk verbatim so the client
                # sees its native `id`, `finish_reason`, `delta.tool_calls`,
                # and final `usage` unchanged.
                yield raw_line + "\n\n"
                if raw_line[6:].strip() == "[DONE]":
                    break
        except Exception as e:
            # Mid-stream failures still have to be reported inside the SSE
            # body because the 200 response headers have already been
            # committed by the time the first chunk flushes.
            logger.error("openai passthrough stream error: %s", e)
            err = {
                "error": {
                    "message": _friendly_error(e),
                    "type": "server_error",
                },
            }
            yield f"data: {json.dumps(err)}\n\n"
        finally:
            if lines_iter is not None:
                try:
                    await lines_iter.aclose()
                except Exception:
                    pass
            try:
                await resp.aclose()
            except Exception:
                pass
            try:
                await client.aclose()
            except Exception:
                pass