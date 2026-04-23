def makedirs(name, mode=0o777, exist_ok=False, *, parent_mode=None):
    """makedirs(name [, mode=0o777][, exist_ok=False][, parent_mode=None])

    Super-mkdir; create a leaf directory and all intermediate ones.  Works like
    mkdir, except that any intermediate path segment (not just the rightmost)
    will be created if it does not exist. If the target directory already
    exists, raise an OSError if exist_ok is False. Otherwise no exception is
    raised.  If parent_mode is not None, it will be used as the mode for any
    newly-created, intermediate-level directories. Otherwise, intermediate
    directories are created with the default permissions (respecting umask).
    This is recursive.

    """
    head, tail = os.path.split(name)
    if not tail:
        head, tail = os.path.split(head)
    if head and tail and not os.path.exists(head):
        try:
            if parent_mode is not None:
                makedirs(
                    head, mode=parent_mode, exist_ok=exist_ok, parent_mode=parent_mode
                )
            else:
                makedirs(head, exist_ok=exist_ok)
        except FileExistsError:
            # Defeats race condition when another thread created the path
            pass
        cdir = curdir
        if isinstance(tail, bytes):
            cdir = bytes(curdir, "ASCII")
        if tail == cdir:  # xxx/newdir/. exists if xxx/newdir exists
            return
    try:
        os.mkdir(name, mode)
        # PY315: The call to `chmod()` is not in the CPython proposed code.
        # Apply `chmod()` after `mkdir()` to enforce the exact requested
        # permissions, since the kernel masks the mode argument with the
        # process umask. This guarantees consistent directory permissions
        # without mutating global umask state.
        os.chmod(name, mode)
    except OSError:
        # Cannot rely on checking for EEXIST, since the operating system
        # could give priority to other errors like EACCES or EROFS
        if not exist_ok or not os.path.isdir(name):
            raise