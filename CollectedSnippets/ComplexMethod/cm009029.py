def _collect_output(
        self,
        marker: str,
        deadline: float,
        timeout: float,
    ) -> CommandExecutionResult:
        collected: list[str] = []
        total_lines = 0
        total_bytes = 0
        truncated_by_lines = False
        truncated_by_bytes = False
        exit_code: int | None = None
        timed_out = False

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                timed_out = True
                break
            try:
                source, data = self._queue.get(timeout=remaining)
            except queue.Empty:
                timed_out = True
                break

            if data is None:
                continue

            if source == "stdout" and data.startswith(marker):
                _, _, status = data.partition(" ")
                exit_code = self._safe_int(status.strip())
                # Drain any remaining stderr that may have arrived concurrently.
                # The stderr reader thread runs independently, so output might
                # still be in flight when the stdout marker arrives.
                self._drain_remaining_stderr(collected, deadline)
                break

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

        if timed_out:
            LOGGER.warning(
                "Command timed out after %.2f seconds; restarting shell session.",
                timeout,
            )
            self.restart()
            return CommandExecutionResult(
                output="",
                exit_code=None,
                timed_out=True,
                truncated_by_lines=truncated_by_lines,
                truncated_by_bytes=truncated_by_bytes,
                total_lines=total_lines,
                total_bytes=total_bytes,
            )

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