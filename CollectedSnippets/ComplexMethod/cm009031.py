def _run_shell_tool(
        self,
        resources: _SessionResources,
        payload: dict[str, Any],
        *,
        tool_call_id: str | None,
    ) -> Any:
        session = resources.session

        if payload.get("restart"):
            LOGGER.info("Restarting shell session on request.")
            try:
                session.restart()
                self._run_startup_commands(session)
            except BaseException as err:
                LOGGER.exception("Restarting shell session failed; session remains unavailable.")
                msg = "Failed to restart shell session."
                raise ToolException(msg) from err
            message = "Shell session restarted."
            return self._format_tool_message(message, tool_call_id, status="success")

        command = payload.get("command")
        if not command or not isinstance(command, str):
            msg = "Shell tool expects a 'command' string when restart is not requested."
            raise ToolException(msg)

        LOGGER.info("Executing shell command: %s", command)
        result = session.execute(command, timeout=self._execution_policy.command_timeout)

        if result.timed_out:
            timeout_seconds = self._execution_policy.command_timeout
            message = f"Error: Command timed out after {timeout_seconds:.1f} seconds."
            return self._format_tool_message(
                message,
                tool_call_id,
                status="error",
                artifact={
                    "timed_out": True,
                    "exit_code": None,
                },
            )

        try:
            sanitized_output, matches = self._apply_redactions(result.output)
        except PIIDetectionError as error:
            LOGGER.warning("Blocking command output due to detected %s.", error.pii_type)
            message = f"Output blocked: detected {error.pii_type}."
            return self._format_tool_message(
                message,
                tool_call_id,
                status="error",
                artifact={
                    "timed_out": False,
                    "exit_code": result.exit_code,
                    "matches": {error.pii_type: error.matches},
                },
            )

        sanitized_output = sanitized_output or "<no output>"
        if result.truncated_by_lines:
            sanitized_output = (
                f"{sanitized_output.rstrip()}\n\n"
                f"... Output truncated at {self._execution_policy.max_output_lines} lines "
                f"(observed {result.total_lines})."
            )
        if result.truncated_by_bytes and self._execution_policy.max_output_bytes is not None:
            sanitized_output = (
                f"{sanitized_output.rstrip()}\n\n"
                f"... Output truncated at {self._execution_policy.max_output_bytes} bytes "
                f"(observed {result.total_bytes})."
            )

        if result.exit_code not in {0, None}:
            sanitized_output = f"{sanitized_output.rstrip()}\n\nExit code: {result.exit_code}"
            final_status: Literal["success", "error"] = "error"
        else:
            final_status = "success"

        artifact = {
            "timed_out": False,
            "exit_code": result.exit_code,
            "truncated_by_lines": result.truncated_by_lines,
            "truncated_by_bytes": result.truncated_by_bytes,
            "total_lines": result.total_lines,
            "total_bytes": result.total_bytes,
            "redaction_matches": matches,
        }

        return self._format_tool_message(
            sanitized_output,
            tool_call_id,
            status=final_status,
            artifact=artifact,
        )