async def run(
        self,
        input_data: Input,
        *,
        execution_context: ExecutionContext,
        **kwargs,
    ) -> BlockOutput:
        """Validate inputs, invoke the autopilot, and yield structured outputs.

        Yields session_id even on failure so callers can inspect/resume the session.
        """
        if not input_data.prompt.strip():
            yield "error", "Prompt cannot be empty."
            return

        if not execution_context.user_id:
            yield "error", "Cannot run autopilot without an authenticated user."
            return

        if input_data.max_recursion_depth < 1:
            yield "error", "max_recursion_depth must be at least 1."
            return

        # Validate and build permissions eagerly — fail before creating a session.
        permissions = await _build_and_validate_permissions(input_data)
        if isinstance(permissions, str):
            # Validation error returned as a string message.
            yield "error", permissions
            return

        # Create session eagerly so the user always gets the session_id,
        # even if the downstream stream fails (avoids orphaned sessions).
        sid = input_data.session_id
        if not sid:
            sid = await self.create_session(
                execution_context.user_id,
                dry_run=input_data.dry_run or execution_context.dry_run,
            )

        # NOTE: No asyncio.timeout() here — the SDK manages its own
        # heartbeat-based timeouts internally.  Wrapping with asyncio.timeout
        # would cancel the task mid-flight, corrupting the SDK's internal
        # anyio memory stream (see service.py CRITICAL comment).
        try:
            response, tool_calls, history, _, usage = await self.execute_copilot(
                prompt=input_data.prompt,
                system_context=input_data.system_context,
                session_id=sid,
                max_recursion_depth=input_data.max_recursion_depth,
                user_id=execution_context.user_id,
                permissions=permissions,
            )

            yield "response", response
            yield "tool_calls", tool_calls
            yield "conversation_history", history
            yield "session_id", sid
            yield "token_usage", usage
        except asyncio.CancelledError:
            yield "session_id", sid
            yield "error", "AutoPilot execution was cancelled."
            raise
        except SubAgentRecursionError as exc:
            # Deliberate block — re-enqueueing would immediately hit the limit
            # again, so skip recovery and just surface the error.
            yield "session_id", sid
            yield "error", str(exc)
        except Exception as exc:
            yield "session_id", sid
            # Recovery enqueue must happen BEFORE yielding "error": the block
            # framework (_base.execute) raises BlockExecutionError immediately
            # when it sees ("error", ...) and stops consuming the generator,
            # so any code after that yield is dead code in production.
            effective_prompt = input_data.prompt
            if input_data.system_context:
                effective_prompt = (
                    f"[System Context: {input_data.system_context}]\n\n"
                    f"{input_data.prompt}"
                )
            try:
                await _enqueue_for_recovery(
                    sid,
                    execution_context.user_id,
                    effective_prompt,
                    input_data.dry_run or execution_context.dry_run,
                )
            except asyncio.CancelledError:
                # Task cancelled during recovery — still yield the error
                # so the session_id + error pair is visible before re-raising.
                yield "error", str(exc)
                raise
            except Exception:
                logger.warning(
                    "AutoPilot session %s: recovery enqueue raised unexpectedly",
                    sid[:12],
                    exc_info=True,
                )
            yield "error", str(exc)