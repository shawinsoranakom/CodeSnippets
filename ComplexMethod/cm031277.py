def pipe(*, duplex=False, overlapped=(True, True), bufsize=BUFSIZE):
    """Like os.pipe() but with overlapped support and using handles not fds."""
    if duplex:
        openmode = _winapi.PIPE_ACCESS_DUPLEX
        access = _winapi.GENERIC_READ | _winapi.GENERIC_WRITE
        obsize, ibsize = bufsize, bufsize
    else:
        openmode = _winapi.PIPE_ACCESS_INBOUND
        access = _winapi.GENERIC_WRITE
        obsize, ibsize = 0, bufsize

    openmode |= _winapi.FILE_FLAG_FIRST_PIPE_INSTANCE

    if overlapped[0]:
        openmode |= _winapi.FILE_FLAG_OVERLAPPED

    if overlapped[1]:
        flags_and_attribs = _winapi.FILE_FLAG_OVERLAPPED
    else:
        flags_and_attribs = 0

    h1 = h2 = None
    try:
        for attempts in itertools.count():
            address = r'\\.\pipe\python-pipe-{:d}-{:d}-{}'.format(
                os.getpid(), next(_mmap_counter), os.urandom(8).hex())
            try:
                h1 = _winapi.CreateNamedPipe(
                    address, openmode, _winapi.PIPE_WAIT,
                    1, obsize, ibsize, _winapi.NMPWAIT_WAIT_FOREVER, _winapi.NULL)
                break
            except OSError as e:
                if attempts >= _MAX_PIPE_ATTEMPTS:
                    raise
                if e.winerror not in (_winapi.ERROR_PIPE_BUSY,
                                      _winapi.ERROR_ACCESS_DENIED):
                    raise

        h2 = _winapi.CreateFile(
            address, access, 0, _winapi.NULL, _winapi.OPEN_EXISTING,
            flags_and_attribs, _winapi.NULL)

        ov = _winapi.ConnectNamedPipe(h1, overlapped=True)
        ov.GetOverlappedResult(True)
        return h1, h2
    except:
        if h1 is not None:
            _winapi.CloseHandle(h1)
        if h2 is not None:
            _winapi.CloseHandle(h2)
        raise