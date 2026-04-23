def __init__(self, args, stdin=None, stdout=None, stderr=None, **kwds):
        assert not kwds.get('universal_newlines')
        assert kwds.get('bufsize', 0) == 0
        stdin_rfd = stdout_wfd = stderr_wfd = None
        stdin_wh = stdout_rh = stderr_rh = None
        if stdin == PIPE:
            stdin_rh, stdin_wh = pipe(overlapped=(False, True), duplex=True)
            stdin_rfd = msvcrt.open_osfhandle(stdin_rh, os.O_RDONLY)
        else:
            stdin_rfd = stdin
        if stdout == PIPE:
            stdout_rh, stdout_wh = pipe(overlapped=(True, False))
            stdout_wfd = msvcrt.open_osfhandle(stdout_wh, 0)
        else:
            stdout_wfd = stdout
        if stderr == PIPE:
            stderr_rh, stderr_wh = pipe(overlapped=(True, False))
            stderr_wfd = msvcrt.open_osfhandle(stderr_wh, 0)
        elif stderr == STDOUT:
            stderr_wfd = stdout_wfd
        else:
            stderr_wfd = stderr
        try:
            super().__init__(args, stdin=stdin_rfd, stdout=stdout_wfd,
                             stderr=stderr_wfd, **kwds)
        except:
            for h in (stdin_wh, stdout_rh, stderr_rh):
                if h is not None:
                    _winapi.CloseHandle(h)
            raise
        else:
            if stdin_wh is not None:
                self.stdin = PipeHandle(stdin_wh)
            if stdout_rh is not None:
                self.stdout = PipeHandle(stdout_rh)
            if stderr_rh is not None:
                self.stderr = PipeHandle(stderr_rh)
        finally:
            if stdin == PIPE:
                os.close(stdin_rfd)
            if stdout == PIPE:
                os.close(stdout_wfd)
            if stderr == PIPE:
                os.close(stderr_wfd)