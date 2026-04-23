def _fastcopy_sendfile(fsrc, fdst):
    """Copy data from one regular mmap-like fd to another by using
    high-performance sendfile(2) syscall.
    This should work on Linux >= 2.6.33, Android and Solaris.
    """
    # Note: copyfileobj() is left alone in order to not introduce any
    # unexpected breakage. Possible risks by using zero-copy calls
    # in copyfileobj() are:
    # - fdst cannot be open in "a"(ppend) mode
    # - fsrc and fdst may be open in "t"(ext) mode
    # - fsrc may be a BufferedReader (which hides unread data in a buffer),
    #   GzipFile (which decompresses data), HTTPResponse (which decodes
    #   chunks).
    # - possibly others (e.g. encrypted fs/partition?)
    global _USE_CP_SENDFILE
    try:
        infd = fsrc.fileno()
        outfd = fdst.fileno()
    except Exception as err:
        raise _GiveupOnFastCopy(err)  # not a regular file

    blocksize = _determine_linux_fastcopy_blocksize(infd)
    offset = 0
    while True:
        try:
            sent = os.sendfile(outfd, infd, offset, blocksize)
        except OSError as err:
            # ...in order to have a more informative exception.
            err.filename = fsrc.name
            err.filename2 = fdst.name

            if err.errno == errno.ENOTSOCK:
                # sendfile() on this platform (probably Linux < 2.6.33)
                # does not support copies between regular files (only
                # sockets).
                _USE_CP_SENDFILE = False
                raise _GiveupOnFastCopy(err)

            if err.errno == errno.ENOSPC:  # filesystem is full
                raise err from None

            # Give up on first call and if no data was copied.
            if offset == 0 and os.lseek(outfd, 0, os.SEEK_CUR) == 0:
                raise _GiveupOnFastCopy(err)

            raise err
        else:
            if sent == 0:
                break  # EOF
            offset += sent