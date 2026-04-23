def _collect_output_after_exit(self, deadline: float) -> CommandExecutionResult:
        """Collect output after the shell exited unexpectedly.

        Called when a `BrokenPipeError` occurs while writing to stdin, indicating the
        shell process terminated (e.g., due to an 'exit' command).

        Args:
            deadline: Absolute time by which collection must complete.

        Returns:
            `CommandExecutionResult` with collected output and the process exit code.
        """
        collected: list[str] = []
        total_lines = 0
        total_bytes = 0
        truncated_by_lines = False
        truncated_by_bytes = False

        # Give reader threads a brief moment to enqueue any remaining output.
        drain_timeout = 0.1
        drain_deadline = min(time.monotonic() + drain_timeout, deadline)

        while True:
            remaining = drain_deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                source, data = self._queue.get(timeout=remaining)
            except queue.Empty:
                break

            if data is None:
                # EOF marker from a reader thread; continue draining.
                continue

            total_lines += 1
            encoded = data.encode("utf-8", "replace")
            total_bytes += len(encoded)

            if total_lines > self._policy.max_output_lines:
                truncated_by_lines = True
                continue

            if (
                self._policy.max_output_bytes is not None
                and total_bytes > self._policy.max_output_bytes
            ):
                truncated_by_bytes = True
                continue

            if source == "stderr":
                stripped = data.rstrip("\n")
                collected.append(f"[stderr] {stripped}")
                if data.endswith("\n"):
                    collected.append("\n")
            else:
                collected.append(data)

        # Get exit code from the terminated process.
        exit_code: int | None = None
        if self._process:
            exit_code = self._process.poll()

        output = "".join(collected)
        return CommandExecutionResult(
            output=output,
            exit_code=exit_code,
            timed_out=False,
            truncated_by_lines=truncated_by_lines,
            truncated_by_bytes=truncated_by_bytes,
            total_lines=total_lines,
            total_bytes=total_bytes,
        )