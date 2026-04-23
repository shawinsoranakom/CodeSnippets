async def _stream():
            # Manual httpx client/response lifecycle AND explicit
            # aiter_bytes() iterator close — see _anthropic_passthrough_stream
            # for the full rationale. Saving `bytes_iter = resp.aiter_bytes()`
            # and `await bytes_iter.aclose()` in the finally block is the
            # part that matters for avoiding the Python 3.13 + httpcore
            # 1.0.x "Exception ignored in: <async_generator>" / anyio
            # cancel-scope trace: an anonymous async for leaves the
            # iterator unclosed, so Python's asyncgen GC finalizer runs
            # cleanup on a later pass in a different asyncio task.
            client = httpx.AsyncClient(timeout = 600)
            resp = None
            bytes_iter = None
            try:
                req = client.build_request("POST", target_url, json = body)
                resp = await client.send(req, stream = True)
                bytes_iter = resp.aiter_bytes()
                async for chunk in bytes_iter:
                    yield chunk
            except Exception as e:
                logger.error("openai_completions stream error: %s", e)
            finally:
                if bytes_iter is not None:
                    try:
                        await bytes_iter.aclose()
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