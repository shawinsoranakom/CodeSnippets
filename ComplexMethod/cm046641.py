def _wait_response(self, expected_type: str, timeout: float = 300.0) -> dict:
        """Block until a response of the expected type arrives.

        Also handles 'status' and 'error' events during the wait.
        Returns the matching response dict.
        Raises RuntimeError on timeout or subprocess crash.

        The *timeout* is an **inactivity** timeout: it resets whenever the
        subprocess sends a status message, so long-running operations (large
        downloads, slow model loads) won't be killed as long as the subprocess
        keeps reporting progress.
        """
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            remaining = max(0.1, deadline - time.monotonic())
            resp = self._read_resp(timeout = min(remaining, 1.0))

            if resp is None:
                # Check subprocess health
                if not self._ensure_subprocess_alive():
                    raise RuntimeError("Inference subprocess crashed during wait")
                continue

            rtype = resp.get("type", "")

            if rtype == expected_type:
                return resp

            if rtype == "error":
                error_msg = resp.get("error", "Unknown error")
                raise RuntimeError(f"Subprocess error: {error_msg}")

            if rtype == "status":
                logger.info("Subprocess status: %s", resp.get("message", ""))
                # Reset deadline — subprocess is still alive and working
                deadline = time.monotonic() + timeout
                continue

            if rtype == "stall":
                msg = resp.get("message", "Download stalled")
                logger.warning("Subprocess reported stall: %s", msg)
                raise DownloadStallError(msg)

            # Other response types during wait — skip
            logger.debug(
                "Skipping response type '%s' while waiting for '%s'",
                rtype,
                expected_type,
            )

        raise RuntimeError(
            f"Timeout waiting for '{expected_type}' response "
            f"(no activity for {timeout}s)"
        )