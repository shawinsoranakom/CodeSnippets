def _wait_response(self, expected_type: str, timeout: float = 3600.0) -> dict:
        """Block until a response of the expected type arrives.

        Export operations can take a very long time — GGUF conversion for
        large models (30B+) easily takes 20-30 minutes. Default timeout
        is 1 hour.
        """
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            remaining = max(0.1, deadline - time.monotonic())
            resp = self._read_resp(timeout = min(remaining, 2.0))

            if resp is None:
                # Check subprocess health
                if not self._ensure_subprocess_alive():
                    raise RuntimeError("Export subprocess crashed during wait")
                continue

            rtype = resp.get("type", "")

            if rtype == expected_type:
                return resp

            if rtype == "error":
                error_msg = resp.get("error", "Unknown error")
                raise RuntimeError(f"Subprocess error: {error_msg}")

            if rtype == "log":
                # Forwarded stdout/stderr line from the worker process.
                self._append_log(resp)
                continue

            if rtype == "status":
                message = resp.get("message", "")
                logger.info("Export subprocess status: %s", message)
                # Surface status messages in the live log panel too so
                # users see high level progress (e.g. "Importing
                # Unsloth...", "Loading checkpoint: ...") alongside
                # subprocess output.
                if message:
                    self._append_log(
                        {
                            "stream": "status",
                            "line": message,
                            "ts": resp.get("ts", time.time()),
                        }
                    )
                continue

            # Other response types during wait — skip
            logger.debug(
                "Skipping response type '%s' while waiting for '%s'",
                rtype,
                expected_type,
            )

        raise RuntimeError(
            f"Timeout waiting for '{expected_type}' response after {timeout}s"
        )