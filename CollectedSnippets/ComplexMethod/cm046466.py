def install_lock(lock_path: Path) -> Iterator[None]:
    lock_path.parent.mkdir(parents = True, exist_ok = True)

    if FileLock is None:
        # Fallback: exclusive file creation as a simple lock.
        # Write our PID so stale locks from crashed processes can be detected.
        fd: int | None = None
        deadline = time.monotonic() + INSTALL_LOCK_TIMEOUT_SECONDS
        while True:
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                try:
                    os.write(fd, f"{os.getpid()}\n".encode())
                    os.fsync(fd)
                except Exception:
                    os.close(fd)
                    fd = None
                    lock_path.unlink(missing_ok = True)
                    raise
                break
            except FileExistsError:
                # Check if the holder process is still alive
                stale = False
                try:
                    raw = lock_path.read_text().strip()
                except FileNotFoundError:
                    # Lock vanished between our open attempt and read -- retry
                    continue
                if not raw:
                    # File exists but PID not yet written -- another process
                    # just created it. Wait briefly for the write to land.
                    if time.monotonic() >= deadline:
                        raise BusyInstallConflict(
                            f"timed out after {INSTALL_LOCK_TIMEOUT_SECONDS}s waiting for concurrent install lock: {lock_path}"
                        )
                    time.sleep(0.1)
                    continue
                try:
                    holder_pid = int(raw)
                    os.kill(holder_pid, 0)  # signal 0 = existence check
                except ValueError:
                    # PID unreadable (corrupted file)
                    stale = True
                except ProcessLookupError:
                    # Process is dead
                    stale = True
                except PermissionError:
                    # Process is alive but owned by another user -- not stale
                    pass
                if stale:
                    lock_path.unlink(missing_ok = True)
                    continue
                if time.monotonic() >= deadline:
                    raise BusyInstallConflict(
                        f"timed out after {INSTALL_LOCK_TIMEOUT_SECONDS}s waiting for concurrent install lock: {lock_path}"
                    )
                time.sleep(0.5)
        try:
            yield
        finally:
            if fd is not None:
                os.close(fd)
            lock_path.unlink(missing_ok = True)
        return

    try:
        with FileLock(lock_path, timeout = INSTALL_LOCK_TIMEOUT_SECONDS):
            yield
    except FileLockTimeout as exc:
        raise BusyInstallConflict(
            f"timed out after {INSTALL_LOCK_TIMEOUT_SECONDS}s waiting for concurrent install lock: {lock_path}"
        ) from exc