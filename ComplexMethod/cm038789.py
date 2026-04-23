def _get_open_port(
    start_port: int | None = None,
    max_attempts: int | None = None,
) -> int:
    start_port = start_port if start_port is not None else envs.VLLM_PORT
    port = start_port
    if port is not None:
        attempts = 0
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("", port))
                    return port
            except OSError:
                port += 1  # Increment port number if already in use
                logger.info("Port %d is already in use, trying port %d", port - 1, port)
            attempts += 1
            if max_attempts is not None and attempts >= max_attempts:
                raise RuntimeError(
                    f"Could not find open port after {max_attempts} "
                    f"attempts starting from port {start_port}"
                )
    # try ipv4
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]
    except OSError:
        # try ipv6
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]