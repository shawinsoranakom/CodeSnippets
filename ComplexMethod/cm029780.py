def realpath(filename, /, *, strict=False):
    """Return the canonical path of the specified filename, eliminating any
symbolic links encountered in the path."""
    filename = os.fspath(filename)
    if isinstance(filename, bytes):
        sep = b'/'
        curdir = b'.'
        pardir = b'..'
        getcwd = os.getcwdb
    else:
        sep = '/'
        curdir = '.'
        pardir = '..'
        getcwd = os.getcwd
    if strict is ALLOW_MISSING:
        ignored_error = FileNotFoundError
    elif strict is ALL_BUT_LAST:
        ignored_error = FileNotFoundError
    elif strict:
        ignored_error = ()
    else:
        ignored_error = OSError

    lstat = os.lstat
    readlink = os.readlink
    maxlinks = None

    # The stack of unresolved path parts. When popped, a special value of None
    # indicates that a symlink target has been resolved, and that the original
    # symlink path can be retrieved by popping again. The [::-1] slice is a
    # very fast way of spelling list(reversed(...)).
    rest = filename.rstrip(sep).split(sep)[::-1]

    # Number of unprocessed parts in 'rest'. This can differ from len(rest)
    # later, because 'rest' might contain markers for unresolved symlinks.
    part_count = len(rest)

    # The resolved path, which is absolute throughout this function.
    # Note: getcwd() returns a normalized and symlink-free path.
    path = sep if filename.startswith(sep) else getcwd()
    trailing_sep = filename.endswith(sep)

    # Mapping from symlink paths to *fully resolved* symlink targets. If a
    # symlink is encountered but not yet resolved, the value is None. This is
    # used both to detect symlink loops and to speed up repeated traversals of
    # the same links.
    seen = {}

    # Number of symlinks traversed. When the number of traversals is limited
    # by *maxlinks*, this is used instead of *seen* to detect symlink loops.
    link_count = 0

    while part_count:
        name = rest.pop()
        if name is None:
            # resolved symlink target
            seen[rest.pop()] = path
            continue
        part_count -= 1
        if not name or name == curdir:
            # current dir
            continue
        if name == pardir:
            # parent dir
            path = path[:path.rindex(sep)] or sep
            continue
        if path == sep:
            newpath = path + name
        else:
            newpath = path + sep + name
        try:
            st_mode = lstat(newpath).st_mode
            if not stat.S_ISLNK(st_mode):
                if (strict and (part_count or trailing_sep)
                    and not stat.S_ISDIR(st_mode)):
                    raise OSError(errno.ENOTDIR, os.strerror(errno.ENOTDIR),
                                  newpath)
                path = newpath
                continue
            elif maxlinks is not None:
                link_count += 1
                if link_count > maxlinks:
                    if strict:
                        raise OSError(errno.ELOOP, os.strerror(errno.ELOOP),
                                      newpath)
                    path = newpath
                    continue
            elif newpath in seen:
                # Already seen this path
                path = seen[newpath]
                if path is not None:
                    # use cached value
                    continue
                # The symlink is not resolved, so we must have a symlink loop.
                if strict:
                    raise OSError(errno.ELOOP, os.strerror(errno.ELOOP),
                                  newpath)
                path = newpath
                continue
            target = readlink(newpath)
        except ignored_error:
            if strict is ALL_BUT_LAST and part_count:
                raise
        else:
            # Resolve the symbolic link
            if target.startswith(sep):
                # Symlink target is absolute; reset resolved path.
                path = sep
            if maxlinks is None:
                # Mark this symlink as seen but not fully resolved.
                seen[newpath] = None
                # Push the symlink path onto the stack, and signal its specialness
                # by also pushing None. When these entries are popped, we'll
                # record the fully-resolved symlink target in the 'seen' mapping.
                rest.append(newpath)
                rest.append(None)
            # Push the unresolved symlink target parts onto the stack.
            target_parts = target.split(sep)[::-1]
            rest.extend(target_parts)
            part_count += len(target_parts)
            continue
        # An error occurred and was ignored.
        path = newpath

    return path