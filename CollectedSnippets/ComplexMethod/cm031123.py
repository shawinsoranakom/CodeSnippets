def _wait_for_signal(sock, expected_signals, timeout=SHORT_TIMEOUT):
    """
    Wait for expected signal(s) from a socket with proper timeout and EOF handling.

    Args:
        sock: Connected socket to read from
        expected_signals: Single bytes object or list of bytes objects to wait for
        timeout: Socket timeout in seconds

    Returns:
        bytes: Complete accumulated response buffer

    Raises:
        RuntimeError: If connection closed before signal received or timeout
    """
    if isinstance(expected_signals, bytes):
        expected_signals = [expected_signals]

    sock.settimeout(timeout)
    buffer = b""

    while True:
        # Check if all expected signals are in buffer
        if all(sig in buffer for sig in expected_signals):
            return buffer

        try:
            chunk = sock.recv(4096)
            if not chunk:
                raise RuntimeError(
                    f"Connection closed before receiving expected signals. "
                    f"Expected: {expected_signals}, Got: {buffer[-200:]!r}"
                )
            buffer += chunk
        except socket.timeout:
            raise RuntimeError(
                f"Timeout waiting for signals. "
                f"Expected: {expected_signals}, Got: {buffer[-200:]!r}"
            ) from None
        except OSError as e:
            raise RuntimeError(
                f"Socket error while waiting for signals: {e}. "
                f"Expected: {expected_signals}, Got: {buffer[-200:]!r}"
            ) from None