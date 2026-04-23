def find_available_port_with_lock(
    min_port: int = 30000,
    max_port: int = 39999,
    max_attempts: int = 20,
    bind_address: str = '0.0.0.0',
    lock_timeout: float = 1.0,
) -> Optional[tuple[int, PortLock]]:
    """Find an available port and acquire a lock for it.

    This function combines file-based locking with port availability checking
    to prevent race conditions in multi-process scenarios.

    Args:
        min_port: Minimum port number to try
        max_port: Maximum port number to try
        max_attempts: Maximum number of ports to try
        bind_address: Address to bind to when checking availability
        lock_timeout: Timeout for acquiring port lock

    Returns:
        Tuple of (port, lock) if successful, None otherwise
    """
    rng = random.SystemRandom()

    # Try random ports first for better distribution
    random_attempts = min(max_attempts // 2, 10)
    for _ in range(random_attempts):
        port = rng.randint(min_port, max_port)

        # Try to acquire lock first
        lock = PortLock(port)
        if lock.acquire(timeout=lock_timeout):
            # Check if port is actually available
            if _check_port_available(port, bind_address):
                logger.debug(f'Found and locked available port {port}')
                return port, lock
            else:
                # Port is locked but not available (maybe in TIME_WAIT state)
                lock.release()

        # Small delay to reduce contention
        time.sleep(0.001)

    # If random attempts failed, try sequential search
    remaining_attempts = max_attempts - random_attempts
    start_port = rng.randint(min_port, max_port - remaining_attempts)

    for i in range(remaining_attempts):
        port = start_port + i
        if port > max_port:
            port = min_port + (port - max_port - 1)

        # Try to acquire lock first
        lock = PortLock(port)
        if lock.acquire(timeout=lock_timeout):
            # Check if port is actually available
            if _check_port_available(port, bind_address):
                logger.debug(f'Found and locked available port {port}')
                return port, lock
            else:
                # Port is locked but not available
                lock.release()

        # Small delay to reduce contention
        time.sleep(0.001)

    logger.error(
        f'Could not find and lock available port in range {min_port}-{max_port} after {max_attempts} attempts'
    )
    return None