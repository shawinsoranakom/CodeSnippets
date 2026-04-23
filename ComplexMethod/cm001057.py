async def get_or_create_sandbox(
    session_id: str,
    api_key: str,
    timeout: int,
    template: str = "base",
    on_timeout: Literal["kill", "pause"] = "pause",
) -> AsyncSandbox:
    """Return the existing E2B sandbox for *session_id* or create a new one.

    The sandbox key in Redis serves a dual purpose: it stores the sandbox_id
    and acts as a creation lock via a ``"creating"`` sentinel value.  This
    removes the need for a separate lock key.

    *timeout* controls how long the e2b sandbox may run continuously before
    the ``on_timeout`` lifecycle rule fires (default: 5 min).
    *on_timeout* controls what happens on timeout: ``"pause"`` (default, free)
    or ``"kill"``.  When ``"pause"``, ``auto_resume`` is enabled so paused
    sandboxes wake transparently on SDK activity.
    """
    redis = await get_redis_async()
    key = _sandbox_key(session_id)

    for _ in range(_MAX_WAIT_ATTEMPTS):
        raw = await redis.get(key)
        value = raw.decode() if isinstance(raw, bytes) else raw

        if value and value != _CREATING_SENTINEL:
            # Existing sandbox ID — try to reconnect (auto-resumes if paused).
            sandbox = await _try_reconnect(value, session_id, api_key)
            if sandbox:
                logger.info(
                    "[E2B] Reconnected to %.12s for session %.12s",
                    value,
                    session_id,
                )
                return sandbox
            # _try_reconnect cleared the key — loop to create a new sandbox.
            continue

        if value == _CREATING_SENTINEL:
            # Another coroutine is creating — wait for it to finish.
            await asyncio.sleep(_WAIT_INTERVAL_SECONDS)
            continue

        # No sandbox and no active creation — atomically claim the creation slot.
        claimed = await redis.set(
            key, _CREATING_SENTINEL, nx=True, ex=_CREATION_LOCK_TTL
        )
        if not claimed:
            # Race lost — another coroutine just claimed it.
            await asyncio.sleep(0.1)
            continue

        # We hold the slot — create the sandbox with per-attempt timeout and
        # retry.  The sentinel remains held throughout so concurrent callers
        # for the same session wait rather than racing to create duplicates.
        sandbox: AsyncSandbox | None = None
        try:
            lifecycle = SandboxLifecycle(
                on_timeout=on_timeout,
                auto_resume=on_timeout == "pause",
            )
            # Note: asyncio.wait_for() only cancels the client-side wait;
            # E2B may complete provisioning server-side after a timeout.
            # Since AsyncSandbox.create() returns no sandbox_id before
            # completion, recovery via connect() is not possible and each
            # timed-out attempt may leak a sandbox.  Under the default
            # on_timeout="pause" lifecycle, leaked orphans are paused (not
            # killed) at end_at and persist until explicitly cleaned up.
            # At most _SANDBOX_CREATE_MAX_RETRIES − 1 = 2 sandboxes can
            # leak per incident.
            last_exc: Exception | None = None
            for attempt in range(1, _SANDBOX_CREATE_MAX_RETRIES + 1):
                try:
                    sandbox = await asyncio.wait_for(
                        AsyncSandbox.create(
                            template=template,
                            api_key=api_key,
                            timeout=timeout,
                            lifecycle=lifecycle,
                        ),
                        timeout=_SANDBOX_CREATE_TIMEOUT_SECONDS,
                    )
                    last_exc = None
                    break
                except Exception as exc:
                    last_exc = exc
                    logger.warning(
                        "[E2B] Sandbox creation attempt %d/%d failed for session %.12s: %s",
                        attempt,
                        _SANDBOX_CREATE_MAX_RETRIES,
                        session_id,
                        exc,
                    )
                    if attempt < _SANDBOX_CREATE_MAX_RETRIES:
                        await asyncio.sleep(2 ** (attempt - 1))  # 1 s, 2 s

            if last_exc is not None:
                raise last_exc

            assert sandbox is not None  # guaranteed: last_exc is None iff break was hit
            try:
                await _set_stored_sandbox_id(session_id, sandbox.sandbox_id)
            except Exception:
                # Redis save failed — kill the sandbox to avoid leaking it.
                with contextlib.suppress(Exception):
                    await asyncio.wait_for(
                        sandbox.kill(), timeout=_E2B_API_TIMEOUT_SECONDS
                    )
                raise
        except asyncio.CancelledError:
            # Task cancelled during creation — release the slot so followers
            # are not blocked for the full TTL (120 s).  CancelledError inherits
            # from BaseException, not Exception, so it is not caught above.
            # Kill the sandbox if it was already created to avoid leaking it
            # (can happen when cancellation fires during _set_stored_sandbox_id).
            # Suppress BaseException (including a second CancelledError) so a
            # re-entrant cancellation during cleanup cannot skip the redis.delete.
            with contextlib.suppress(Exception, asyncio.CancelledError):
                await redis.delete(key)
            if sandbox is not None:
                with contextlib.suppress(Exception, asyncio.CancelledError):
                    await asyncio.wait_for(
                        sandbox.kill(), timeout=_E2B_API_TIMEOUT_SECONDS
                    )
            raise
        except Exception:
            # Release the creation slot so other callers can proceed.
            await redis.delete(key)
            raise

        logger.info(
            "[E2B] Created sandbox %.12s for session %.12s",
            sandbox.sandbox_id,
            session_id,
        )
        return sandbox

    raise RuntimeError(f"Could not acquire E2B sandbox for session {session_id[:12]}")