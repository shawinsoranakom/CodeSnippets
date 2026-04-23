async def _execute(
        self,
        user_id: str | None,
        session: ChatSession,
        *,
        sub_session_id: str = "",
        wait_if_running: int = 60,
        cancel: bool = False,
        include_progress: bool = False,
        **kwargs,
    ) -> ToolResponseBase:
        inner_session_id = sub_session_id.strip()
        if not inner_session_id:
            return ErrorResponse(
                message="sub_session_id is required",
                session_id=session.session_id,
            )
        if user_id is None:
            return ErrorResponse(
                message="Authentication required",
                session_id=session.session_id,
            )

        # Ownership check on every call — loads the ChatSession and
        # confirms the caller owns it. Returning the same "not found"
        # shape for "doesn't exist" and "belongs to someone else" avoids
        # leaking session existence.
        sub = await get_chat_session(inner_session_id)
        if sub is None or sub.user_id != user_id:
            return ErrorResponse(
                message=(
                    f"No sub-session with id {inner_session_id}. It may have "
                    "never existed or belongs to another user."
                ),
                session_id=session.session_id,
            )

        started_at = time.monotonic()

        if cancel:
            # Fan out the cancel event. Whichever worker is running the
            # sub will break out of its stream and finalise the session
            # as failed. Return "cancelled" immediately; the sub may
            # still emit a little more output before the worker notices,
            # but the agent doesn't need to wait for that.
            await enqueue_cancel_task(inner_session_id)
            return SubSessionStatusResponse(
                message="Sub-AutoPilot cancel requested.",
                session_id=session.session_id,
                status="cancelled",
                sub_session_id=inner_session_id,
                sub_autopilot_session_id=inner_session_id,
                sub_autopilot_session_link=_sub_session_link(inner_session_id),
                elapsed_seconds=0.0,
            )

        # If a turn is currently running for this session (stream registry
        # meta shows status=running), we can NOT short-circuit on the
        # persisted last assistant message — that message belongs to a
        # PRIOR turn, and surfacing it here would hand the caller stale
        # data while the new turn is mid-flight (sentry r3105409601).
        # Only short-circuit when there's no active turn AND the last
        # persisted message already looks terminal.
        effective_wait = max(0, min(wait_if_running, MAX_SUB_SESSION_WAIT_SECONDS))
        registry_session = await stream_registry.get_session(inner_session_id)
        turn_in_flight = registry_session is not None and (
            getattr(registry_session, "status", "") == "running"
        )
        terminal_result = None if turn_in_flight else _already_terminal_result(sub)
        outcome: SessionOutcome
        result: SessionResult
        if terminal_result is not None:
            outcome, result = "completed", terminal_result
        elif effective_wait > 0:
            outcome, result = await wait_for_session_result(
                session_id=inner_session_id,
                user_id=user_id,
                timeout=effective_wait,
            )
        else:
            outcome, result = "running", SessionResult()

        elapsed = time.monotonic() - started_at

        if outcome == "running" and include_progress:
            # Running + caller wants progress — hand-assemble the response
            # with the progress snapshot attached. response_from_outcome
            # doesn't carry progress, so we build the response here.
            progress = await _build_progress_snapshot(inner_session_id)
            link = _sub_session_link(inner_session_id)
            return SubSessionStatusResponse(
                message=(
                    f"Sub-AutoPilot still running after {elapsed:.0f}s."
                    f"{f' Watch live at {link}.' if link else ''} "
                    "Call again to keep waiting, or cancel=true to abort."
                ),
                session_id=session.session_id,
                status="running",
                sub_session_id=inner_session_id,
                sub_autopilot_session_id=inner_session_id,
                sub_autopilot_session_link=link,
                elapsed_seconds=round(elapsed, 2),
                progress=progress,
            )

        return response_from_outcome(
            outcome=outcome,
            result=result,
            inner_session_id=inner_session_id,
            parent_session_id=session.session_id,
            elapsed=elapsed,
        )