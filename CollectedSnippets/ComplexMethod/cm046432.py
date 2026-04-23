def is_busy_lock_error(exc: BaseException) -> bool:
    if isinstance(exc, BusyInstallConflict):
        return True
    if isinstance(exc, OSError):
        if exc.errno in {
            errno.EACCES,
            errno.EBUSY,
            errno.EPERM,
            errno.ETXTBSY,
        }:
            return True
        if getattr(exc, "winerror", None) in {5, 32, 145}:
            return True
    for message in _os_error_messages(exc):
        if any(
            needle in message
            for needle in (
                "access is denied",
                "being used by another process",
                "device or resource busy",
                "permission denied",
                "text file busy",
                "file is in use",
                "process cannot access the file",
                "cannot create a file when that file already exists",
            )
        ):
            return True
    return False