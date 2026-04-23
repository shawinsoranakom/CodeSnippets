def cleanup_stale_locks(max_age_seconds: int = 300) -> int:
    """Clean up stale lock files.

    Args:
        max_age_seconds: Maximum age of lock files before they're considered stale

    Returns:
        Number of lock files cleaned up
    """
    lock_dir = os.path.join(tempfile.gettempdir(), 'openhands_port_locks')
    if not os.path.exists(lock_dir):
        return 0

    cleaned = 0
    current_time = time.time()

    try:
        for filename in os.listdir(lock_dir):
            if filename.startswith('port_') and filename.endswith('.lock'):
                lock_path = os.path.join(lock_dir, filename)
                try:
                    # Check if lock file is old
                    stat = os.stat(lock_path)
                    if current_time - stat.st_mtime > max_age_seconds:
                        # Try to remove stale lock
                        os.unlink(lock_path)
                        cleaned += 1
                        logger.debug(f'Cleaned up stale lock file: {filename}')
                except (OSError, FileNotFoundError):
                    # File might have been removed by another process
                    pass
    except OSError:
        # Directory might not exist or be accessible
        pass

    if cleaned > 0:
        logger.info(f'Cleaned up {cleaned} stale port lock files')

    return cleaned