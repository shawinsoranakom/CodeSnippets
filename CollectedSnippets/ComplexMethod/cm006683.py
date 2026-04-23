async def _read_stream_non_blocking(self, stream, stream_name: str) -> str:
        """Read from a stream without blocking and log the content.

        Args:
            stream: The stream to read from (stdout or stderr)
            stream_name: Name of the stream for logging ("stdout" or "stderr")

        Returns:
            The content read from the stream (empty string if nothing available)
        """
        if not stream:
            return ""

        try:
            # On Windows, select.select() doesn't work with pipes (only sockets)
            # Use platform-specific approach
            os_type = platform.system()

            if os_type == "Windows":
                # On Windows, select.select() doesn't work with pipes
                # Skip stream reading during monitoring - output will be captured when process terminates
                # This prevents blocking on peek() which can cause the monitoring loop to hang
                return ""
            # On Unix-like systems, use select
            if select.select([stream], [], [], 0)[0]:
                line_bytes = stream.readline()
                if line_bytes:
                    # Decode bytes with error handling
                    line = line_bytes.decode("utf-8", errors="replace") if isinstance(line_bytes, bytes) else line_bytes
                    stripped = line.strip()
                    if stripped:
                        # Log errors at error level, everything else at debug
                        if stream_name == "stderr" and ("ERROR" in stripped or "error" in stripped):
                            await logger.aerror(f"MCP Composer {stream_name}: {stripped}")
                        else:
                            await logger.adebug(f"MCP Composer {stream_name}: {stripped}")
                        return stripped
        except Exception as e:  # noqa: BLE001
            await logger.adebug(f"Error reading {stream_name}: {e}")
        return ""