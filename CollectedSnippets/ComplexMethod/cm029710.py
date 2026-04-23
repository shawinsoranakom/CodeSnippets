def _fastcopy_copy_file_range(fsrc, fdst):
    """Copy data from one regular mmap-like fd to another by using
    a high-performance copy_file_range(2) syscall that gives filesystems
    an opportunity to implement the use of reflinks or server-side copy.

    This should work on Linux >= 4.5 only.
    """
    try:
        infd = fsrc.fileno()
        outfd = fdst.fileno()
    except Exception as err:
        raise _GiveupOnFastCopy(err)  # not a regular file

    blocksize = _determine_linux_fastcopy_blocksize(infd)
    offset = 0
    while True:
        try:
            n_copied = os.copy_file_range(infd, outfd, blocksize, offset_dst=offset)
        except OSError as err:
            # ...in oder to have a more informative exception.
            err.filename = fsrc.name
            err.filename2 = fdst.name

            if err.errno == errno.ENOSPC:  # filesystem is full
                raise err from None

            # Give up on first call and if no data was copied.
            if offset == 0 and os.lseek(outfd, 0, os.SEEK_CUR) == 0:
                raise _GiveupOnFastCopy(err)

            raise err
        else:
            if n_copied == 0:
                # If no bytes have been copied yet, copy_file_range
                # might silently fail.
                # https://lore.kernel.org/linux-fsdevel/20210126233840.GG4626@dread.disaster.area/T/#m05753578c7f7882f6e9ffe01f981bc223edef2b0
                if offset == 0:
                    raise _GiveupOnFastCopy()
                break
            offset += n_copied