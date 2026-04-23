def _execute_child(self, args, executable, preexec_fn, close_fds,
                           pass_fds, cwd, env,
                           startupinfo, creationflags, shell,
                           p2cread, p2cwrite,
                           c2pread, c2pwrite,
                           errread, errwrite,
                           unused_restore_signals,
                           unused_gid, unused_gids, unused_uid,
                           unused_umask,
                           unused_start_new_session, unused_process_group):
            """Execute program (MS Windows version)"""

            assert not pass_fds, "pass_fds not supported on Windows."

            if isinstance(args, str):
                pass
            elif isinstance(args, bytes):
                if shell:
                    raise TypeError('bytes args is not allowed on Windows')
                args = list2cmdline([args])
            elif isinstance(args, os.PathLike):
                if shell:
                    raise TypeError('path-like args is not allowed when '
                                    'shell is true')
                args = list2cmdline([args])
            else:
                args = list2cmdline(args)

            if executable is not None:
                executable = os.fsdecode(executable)

            # Process startup details
            if startupinfo is None:
                startupinfo = STARTUPINFO()
            else:
                # bpo-34044: Copy STARTUPINFO since it is modified above,
                # so the caller can reuse it multiple times.
                startupinfo = startupinfo.copy()

            use_std_handles = -1 not in (p2cread, c2pwrite, errwrite)
            if use_std_handles:
                startupinfo.dwFlags |= _winapi.STARTF_USESTDHANDLES
                startupinfo.hStdInput = p2cread
                startupinfo.hStdOutput = c2pwrite
                startupinfo.hStdError = errwrite

            attribute_list = startupinfo.lpAttributeList
            have_handle_list = bool(attribute_list and
                                    "handle_list" in attribute_list and
                                    attribute_list["handle_list"])

            # If we were given an handle_list or need to create one
            if have_handle_list or (use_std_handles and close_fds):
                if attribute_list is None:
                    attribute_list = startupinfo.lpAttributeList = {}
                handle_list = attribute_list["handle_list"] = \
                    list(attribute_list.get("handle_list", []))

                if use_std_handles:
                    handle_list += [int(p2cread), int(c2pwrite), int(errwrite)]

                handle_list[:] = self._filter_handle_list(handle_list)

                if handle_list:
                    if not close_fds:
                        warnings.warn("startupinfo.lpAttributeList['handle_list'] "
                                      "overriding close_fds", RuntimeWarning)

                    # When using the handle_list we always request to inherit
                    # handles but the only handles that will be inherited are
                    # the ones in the handle_list
                    close_fds = False

            if shell:
                startupinfo.dwFlags |= _winapi.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = _winapi.SW_HIDE
                if not executable:
                    # gh-101283: without a fully-qualified path, before Windows
                    # checks the system directories, it first looks in the
                    # application directory, and also the current directory if
                    # NeedCurrentDirectoryForExePathW(ExeName) is true, so try
                    # to avoid executing unqualified "cmd.exe".
                    comspec = os.environ.get('ComSpec')
                    if not comspec:
                        system_root = os.environ.get('SystemRoot', '')
                        comspec = os.path.join(system_root, 'System32', 'cmd.exe')
                        if not os.path.isabs(comspec):
                            raise FileNotFoundError('shell not found: neither %ComSpec% nor %SystemRoot% is set')
                    if os.path.isabs(comspec):
                        executable = comspec
                else:
                    comspec = executable

                args = '{} /c "{}"'.format (comspec, args)

            if cwd is not None:
                cwd = os.fsdecode(cwd)

            sys.audit("subprocess.Popen", executable, args, cwd, env)

            # Start the process
            try:
                hp, ht, pid, tid = _winapi.CreateProcess(executable, args,
                                         # no special security
                                         None, None,
                                         int(not close_fds),
                                         creationflags,
                                         env,
                                         cwd,
                                         startupinfo)
            finally:
                # Child is launched. Close the parent's copy of those pipe
                # handles that only the child should have open.  You need
                # to make sure that no handles to the write end of the
                # output pipe are maintained in this process or else the
                # pipe will not close when the child process exits and the
                # ReadFile will hang.
                self._close_pipe_fds(p2cread, p2cwrite,
                                     c2pread, c2pwrite,
                                     errread, errwrite)

            # Retain the process handle, but close the thread handle
            self._child_created = True
            self._handle = Handle(hp)
            self.pid = pid
            _winapi.CloseHandle(ht)