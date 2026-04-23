def _use_posix_spawn():
    """Check if posix_spawn() can be used for subprocess.

    subprocess requires a posix_spawn() implementation that properly reports
    errors to the parent process, & sets errno on the following failures:

    * Process attribute actions failed.
    * File actions failed.
    * exec() failed.

    Prefer an implementation which can use vfork() in some cases for best
    performance.
    """
    if _mswindows or not hasattr(os, 'posix_spawn'):
        # os.posix_spawn() is not available
        return False

    if ((_env := os.environ.get('_PYTHON_SUBPROCESS_USE_POSIX_SPAWN')) in ('0', '1')):
        return bool(int(_env))

    if sys.platform in ('darwin', 'sunos5'):
        # posix_spawn() is a syscall on both macOS and Solaris,
        # and properly reports errors
        return True

    # Check libc name and runtime libc version
    try:
        ver = os.confstr('CS_GNU_LIBC_VERSION')
        # parse 'glibc 2.28' as ('glibc', (2, 28))
        parts = ver.split(maxsplit=1)
        if len(parts) != 2:
            # reject unknown format
            raise ValueError
        libc = parts[0]
        version = tuple(map(int, parts[1].split('.')))

        if sys.platform == 'linux' and libc == 'glibc' and version >= (2, 24):
            # glibc 2.24 has a new Linux posix_spawn implementation using vfork
            # which properly reports errors to the parent process.
            return True
        # Note: Don't use the implementation in earlier glibc because it doesn't
        # use vfork (even if glibc 2.26 added a pipe to properly report errors
        # to the parent process).
    except (AttributeError, ValueError, OSError):
        # os.confstr() or CS_GNU_LIBC_VERSION value not available
        pass

    # By default, assume that posix_spawn() does not properly report errors.
    return False