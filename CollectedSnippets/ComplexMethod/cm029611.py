def __init__(self, args, bufsize=-1, executable=None,
                 stdin=None, stdout=None, stderr=None,
                 preexec_fn=None, close_fds=True,
                 shell=False, cwd=None, env=None, universal_newlines=None,
                 startupinfo=None, creationflags=0,
                 restore_signals=True, start_new_session=False,
                 pass_fds=(), *, user=None, group=None, extra_groups=None,
                 encoding=None, errors=None, text=None, umask=-1, pipesize=-1,
                 process_group=None):
        """Create new Popen instance."""
        if not _can_fork_exec:
            raise OSError(
                errno.ENOTSUP, f"{sys.platform} does not support processes."
            )

        _cleanup()
        # Held while anything is calling waitpid before returncode has been
        # updated to prevent clobbering returncode if wait() or poll() are
        # called from multiple threads at once.  After acquiring the lock,
        # code must re-check self.returncode to see if another thread just
        # finished a waitpid() call.
        self._waitpid_lock = threading.Lock()

        self._input = None
        self._communication_started = False
        if bufsize is None:
            bufsize = -1  # Restore default
        if not isinstance(bufsize, int):
            raise TypeError("bufsize must be an integer")

        if stdout is STDOUT:
            raise ValueError("STDOUT can only be used for stderr")

        if pipesize is None:
            pipesize = -1  # Restore default
        if not isinstance(pipesize, int):
            raise TypeError("pipesize must be an integer")

        if _mswindows:
            if preexec_fn is not None:
                raise ValueError("preexec_fn is not supported on Windows "
                                 "platforms")
        else:
            # POSIX
            if pass_fds and not close_fds:
                warnings.warn("pass_fds overriding close_fds.", RuntimeWarning)
                close_fds = True
            if startupinfo is not None:
                raise ValueError("startupinfo is only supported on Windows "
                                 "platforms")
            if creationflags != 0:
                raise ValueError("creationflags is only supported on Windows "
                                 "platforms")

        self.args = args
        self.stdin = None
        self.stdout = None
        self.stderr = None
        self.pid = None
        self.returncode = None
        self.encoding = encoding
        self.errors = errors
        self.pipesize = pipesize

        # Validate the combinations of text and universal_newlines
        if (text is not None and universal_newlines is not None
            and bool(universal_newlines) != bool(text)):
            raise SubprocessError('Cannot disambiguate when both text '
                                  'and universal_newlines are supplied but '
                                  'different. Pass one or the other.')

        self.text_mode = encoding or errors or text or universal_newlines
        if self.text_mode and encoding is None:
            self.encoding = encoding = _text_encoding()

        # How long to resume waiting on a child after the first ^C.
        # There is no right value for this.  The purpose is to be polite
        # yet remain good for interactive users trying to exit a tool.
        self._sigint_wait_secs = 0.25  # 1/xkcd221.getRandomNumber()

        self._closed_child_pipe_fds = False

        if self.text_mode:
            if bufsize == 1:
                line_buffering = True
                # Use the default buffer size for the underlying binary streams
                # since they don't support line buffering.
                bufsize = -1
            else:
                line_buffering = False

        if process_group is None:
            process_group = -1  # The internal APIs are int-only

        gid = None
        if group is not None:
            if not hasattr(os, 'setregid'):
                raise ValueError("The 'group' parameter is not supported on the "
                                 "current platform")

            elif isinstance(group, str):
                try:
                    import grp
                except ImportError:
                    raise ValueError("The group parameter cannot be a string "
                                     "on systems without the grp module")

                gid = grp.getgrnam(group).gr_gid
            elif isinstance(group, int):
                gid = group
            else:
                raise TypeError("Group must be a string or an integer, not {}"
                                .format(type(group)))

            if gid < 0:
                raise ValueError(f"Group ID cannot be negative, got {gid}")

        gids = None
        if extra_groups is not None:
            if not hasattr(os, 'setgroups'):
                raise ValueError("The 'extra_groups' parameter is not "
                                 "supported on the current platform")

            elif isinstance(extra_groups, str):
                raise ValueError("Groups must be a list, not a string")

            gids = []
            for extra_group in extra_groups:
                if isinstance(extra_group, str):
                    try:
                        import grp
                    except ImportError:
                        raise ValueError("Items in extra_groups cannot be "
                                         "strings on systems without the "
                                         "grp module")

                    gids.append(grp.getgrnam(extra_group).gr_gid)
                elif isinstance(extra_group, int):
                    gids.append(extra_group)
                else:
                    raise TypeError("Items in extra_groups must be a string "
                                    "or integer, not {}"
                                    .format(type(extra_group)))

            # make sure that the gids are all positive here so we can do less
            # checking in the C code
            for gid_check in gids:
                if gid_check < 0:
                    raise ValueError(f"Group ID cannot be negative, got {gid_check}")

        uid = None
        if user is not None:
            if not hasattr(os, 'setreuid'):
                raise ValueError("The 'user' parameter is not supported on "
                                 "the current platform")

            elif isinstance(user, str):
                try:
                    import pwd
                except ImportError:
                    raise ValueError("The user parameter cannot be a string "
                                     "on systems without the pwd module")
                uid = pwd.getpwnam(user).pw_uid
            elif isinstance(user, int):
                uid = user
            else:
                raise TypeError("User must be a string or an integer")

            if uid < 0:
                raise ValueError(f"User ID cannot be negative, got {uid}")

        # Input and output objects. The general principle is like
        # this:
        #
        # Parent                   Child
        # ------                   -----
        # p2cwrite   ---stdin--->  p2cread
        # c2pread    <--stdout---  c2pwrite
        # errread    <--stderr---  errwrite
        #
        # On POSIX, the child objects are file descriptors.  On
        # Windows, these are Windows file handles.  The parent objects
        # are file descriptors on both platforms.  The parent objects
        # are -1 when not using PIPEs. The child objects are -1
        # when not redirecting.

        (p2cread, p2cwrite,
         c2pread, c2pwrite,
         errread, errwrite) = self._get_handles(stdin, stdout, stderr)

        # From here on, raising exceptions may cause file descriptor leakage

        # We wrap OS handles *before* launching the child, otherwise a
        # quickly terminating child could make our fds unwrappable
        # (see #8458).

        if _mswindows:
            if p2cwrite != -1:
                p2cwrite = msvcrt.open_osfhandle(p2cwrite.Detach(), 0)
            if c2pread != -1:
                c2pread = msvcrt.open_osfhandle(c2pread.Detach(), 0)
            if errread != -1:
                errread = msvcrt.open_osfhandle(errread.Detach(), 0)

        try:
            if p2cwrite != -1:
                self.stdin = io.open(p2cwrite, 'wb', bufsize)
                if self.text_mode:
                    self.stdin = io.TextIOWrapper(self.stdin, write_through=True,
                            line_buffering=line_buffering,
                            encoding=encoding, errors=errors)
            if c2pread != -1:
                self.stdout = io.open(c2pread, 'rb', bufsize)
                if self.text_mode:
                    self.stdout = io.TextIOWrapper(self.stdout,
                            encoding=encoding, errors=errors)
            if errread != -1:
                self.stderr = io.open(errread, 'rb', bufsize)
                if self.text_mode:
                    self.stderr = io.TextIOWrapper(self.stderr,
                            encoding=encoding, errors=errors)

            self._execute_child(args, executable, preexec_fn, close_fds,
                                pass_fds, cwd, env,
                                startupinfo, creationflags, shell,
                                p2cread, p2cwrite,
                                c2pread, c2pwrite,
                                errread, errwrite,
                                restore_signals,
                                gid, gids, uid, umask,
                                start_new_session, process_group)
        except:
            # Cleanup if the child failed starting.
            for f in filter(None, (self.stdin, self.stdout, self.stderr)):
                try:
                    f.close()
                except OSError:
                    pass  # Ignore EBADF or other errors.

            if not self._closed_child_pipe_fds:
                to_close = []
                if stdin == PIPE:
                    to_close.append(p2cread)
                if stdout == PIPE:
                    to_close.append(c2pwrite)
                if stderr == PIPE:
                    to_close.append(errwrite)
                if hasattr(self, '_devnull'):
                    to_close.append(self._devnull)
                for fd in to_close:
                    try:
                        if _mswindows and isinstance(fd, Handle):
                            fd.Close()
                        else:
                            os.close(fd)
                    except OSError:
                        pass

            raise