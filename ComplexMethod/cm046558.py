async def _openai_passthrough_stream(
    request,
    cancel_event,
    llama_backend,
    payload,
    model_name,
    completion_id,
):
    """Streaming client-side pass-through for /v1/chat/completions.

    Forwards the client's OpenAI function-calling request to llama-server and
    relays the SSE stream back verbatim. This preserves llama-server's
    native response ``id``, ``finish_reason`` (including ``"tool_calls"``),
    ``delta.tool_calls``, and the trailing ``usage`` chunk so the client
    observes a standard OpenAI response.
    """
    target_url = f"{llama_backend.base_url}/v1/chat/completions"
    body = _build_openai_passthrough_body(payload)

    # Dispatch the upstream request BEFORE returning StreamingResponse so
    # transport errors and non-200 upstream statuses surface as real HTTP
    # errors to the client. OpenAI SDKs rely on status codes to raise
    # ``APIError``/``BadRequestError``/...; burying the failure inside a
    # 200 SSE ``error`` frame silently breaks their error handling.
    client = httpx.AsyncClient(timeout = 600)
    resp = None
    try:
        req = client.build_request("POST", target_url, json = body)
        resp = await client.send(req, stream = True)
    except httpx.RequestError as e:
        # llama-server subprocess crashed / still starting / unreachable.
        logger.error("openai passthrough stream: upstream unreachable: %s", e)
        if resp is not None:
            try:
                await resp.aclose()
            except Exception:
                pass
        try:
            await client.aclose()
        except Exception:
            pass
        raise HTTPException(
            status_code = 502,
            detail = _friendly_error(e),
        )

    if resp.status_code != 200:
        err_bytes = await resp.aread()
        err_text = err_bytes.decode("utf-8", errors = "replace")
        logger.error(
            "openai passthrough upstream error: status=%s body=%s",
            resp.status_code,
            err_text[:500],
        )
        upstream_status = resp.status_code
        try:
            await resp.aclose()
        except Exception:
            pass
        try:
            await client.aclose()
        except Exception:
            pass
        raise HTTPException(
            status_code = upstream_status,
            detail = f"llama-server error: {err_text[:500]}",
        )

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

    return StreamingResponse(
        _stream(),
        media_type = "text/event-stream",
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )