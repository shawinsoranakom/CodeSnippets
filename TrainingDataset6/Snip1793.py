def _read(f, fd):
    data = os.read(fd, 1024)
    try:
        f.write(data)
    except ValueError:
        position = const.LOG_SIZE_IN_BYTES - const.LOG_SIZE_TO_CLEAN
        f.move(0, const.LOG_SIZE_TO_CLEAN, position)
        f.seek(position)
        f.write(b'\x00' * const.LOG_SIZE_TO_CLEAN)
        f.seek(position)
    return data