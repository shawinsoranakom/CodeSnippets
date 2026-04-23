async def disconnect_all_listeners(session_id: str) -> int:
    """Cancel every active listener task for *session_id*.

    Called when the frontend switches away from a session and wants the
    backend to release resources immediately rather than waiting for the
    XREAD timeout.

    Scope / limitations (best-effort optimisation, not a correctness primitive):
    - Pod-local: ``_listener_sessions`` is in-memory. If the DELETE request
      lands on a different worker than the one serving the SSE, no listener
      is cancelled here — the SSE worker still releases on its XREAD timeout.
    - Session-scoped (not subscriber-scoped): cancels every active listener
      for the session on this pod. In the rare case a single user opens two
      SSE connections to the same session on the same pod (e.g. two tabs),
      both would be torn down. Cross-pod, subscriber-scoped cancellation
      would require a Redis pub/sub fan-out with per-listener tokens; that
      is not implemented here because the XREAD timeout already bounds the
      worst case.

    Returns the number of listener tasks that were cancelled.
    """
    to_cancel: list[tuple[int, asyncio.Task]] = [
        (qid, task)
        for qid, (sid, task) in list(_listener_sessions.items())
        if sid == session_id and not task.done()
    ]

    for qid, task in to_cancel:
        _listener_sessions.pop(qid, None)
        task.cancel()

    cancelled = 0
    for _qid, task in to_cancel:
        try:
            await asyncio.wait_for(task, timeout=5.0)
        except asyncio.CancelledError:
            cancelled += 1
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            logger.error(f"Error cancelling listener for session {session_id}: {e}")

    if cancelled:
        logger.info(f"Disconnected {cancelled} listener(s) for session {session_id}")
    return cancelled