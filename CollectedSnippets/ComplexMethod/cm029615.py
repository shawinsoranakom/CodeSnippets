def _get_handles(self, stdin, stdout, stderr):
            """Construct and return tuple with IO objects:
            p2cread, p2cwrite, c2pread, c2pwrite, errread, errwrite
            """
            if stdin is None and stdout is None and stderr is None:
                return (-1, -1, -1, -1, -1, -1)

            p2cread, p2cwrite = -1, -1
            c2pread, c2pwrite = -1, -1
            errread, errwrite = -1, -1

            with self._on_error_fd_closer() as err_close_fds:
                if stdin is None:
                    p2cread = _winapi.GetStdHandle(_winapi.STD_INPUT_HANDLE)
                    if p2cread is None:
                        p2cread, _ = _winapi.CreatePipe(None, 0)
                        p2cread = Handle(p2cread)
                        err_close_fds.append(p2cread)
                        _winapi.CloseHandle(_)
                elif stdin == PIPE:
                    p2cread, p2cwrite = _winapi.CreatePipe(None, 0)
                    p2cread, p2cwrite = Handle(p2cread), Handle(p2cwrite)
                    err_close_fds.extend((p2cread, p2cwrite))
                elif stdin == DEVNULL:
                    p2cread = msvcrt.get_osfhandle(self._get_devnull())
                elif isinstance(stdin, int):
                    p2cread = msvcrt.get_osfhandle(stdin)
                else:
                    # Assuming file-like object
                    p2cread = msvcrt.get_osfhandle(stdin.fileno())
                p2cread = self._make_inheritable(p2cread)

                if stdout is None:
                    c2pwrite = _winapi.GetStdHandle(_winapi.STD_OUTPUT_HANDLE)
                    if c2pwrite is None:
                        _, c2pwrite = _winapi.CreatePipe(None, 0)
                        c2pwrite = Handle(c2pwrite)
                        err_close_fds.append(c2pwrite)
                        _winapi.CloseHandle(_)
                elif stdout == PIPE:
                    c2pread, c2pwrite = _winapi.CreatePipe(None, 0)
                    c2pread, c2pwrite = Handle(c2pread), Handle(c2pwrite)
                    err_close_fds.extend((c2pread, c2pwrite))
                elif stdout == DEVNULL:
                    c2pwrite = msvcrt.get_osfhandle(self._get_devnull())
                elif isinstance(stdout, int):
                    c2pwrite = msvcrt.get_osfhandle(stdout)
                else:
                    # Assuming file-like object
                    c2pwrite = msvcrt.get_osfhandle(stdout.fileno())
                c2pwrite = self._make_inheritable(c2pwrite)

                if stderr is None:
                    errwrite = _winapi.GetStdHandle(_winapi.STD_ERROR_HANDLE)
                    if errwrite is None:
                        _, errwrite = _winapi.CreatePipe(None, 0)
                        errwrite = Handle(errwrite)
                        err_close_fds.append(errwrite)
                        _winapi.CloseHandle(_)
                elif stderr == PIPE:
                    errread, errwrite = _winapi.CreatePipe(None, 0)
                    errread, errwrite = Handle(errread), Handle(errwrite)
                    err_close_fds.extend((errread, errwrite))
                elif stderr == STDOUT:
                    errwrite = c2pwrite
                elif stderr == DEVNULL:
                    errwrite = msvcrt.get_osfhandle(self._get_devnull())
                elif isinstance(stderr, int):
                    errwrite = msvcrt.get_osfhandle(stderr)
                else:
                    # Assuming file-like object
                    errwrite = msvcrt.get_osfhandle(stderr.fileno())
                errwrite = self._make_inheritable(errwrite)

            return (p2cread, p2cwrite,
                    c2pread, c2pwrite,
                    errread, errwrite)