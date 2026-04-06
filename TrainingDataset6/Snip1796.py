def shell_logger(output):
    """Logs shell output to the `output`.

    Works like unix script command with `-f` flag.

    """
    if not os.environ.get('SHELL'):
        logs.warn("Shell logger doesn't support your platform.")
        sys.exit(1)

    fd = os.open(output, os.O_CREAT | os.O_TRUNC | os.O_RDWR)
    os.write(fd, b'\x00' * const.LOG_SIZE_IN_BYTES)
    buffer = mmap.mmap(fd, const.LOG_SIZE_IN_BYTES, mmap.MAP_SHARED, mmap.PROT_WRITE)
    return_code = _spawn(os.environ['SHELL'], partial(_read, buffer))

    sys.exit(return_code)