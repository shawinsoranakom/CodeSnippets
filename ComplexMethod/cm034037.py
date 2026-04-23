def run_command(self, args, check_rc=False, close_fds=True, executable=None, data=None, binary_data=False, path_prefix=None, cwd=None,
                    use_unsafe_shell=False, prompt_regex=None, environ_update=None, umask=None, encoding='utf-8', errors='surrogate_or_strict',
                    expand_user_and_vars=True, pass_fds=None, before_communicate_callback=None, ignore_invalid_cwd=True, handle_exceptions=True):
        """
        Execute a command, returns rc, stdout, and stderr.

        The mechanism of this method for reading stdout and stderr differs from
        that of CPython subprocess.Popen.communicate, in that this method will
        stop reading once the spawned command has exited and stdout and stderr
        have been consumed, as opposed to waiting until stdout/stderr are
        closed. This can be an important distinction, when taken into account
        that a forked or backgrounded process may hold stdout or stderr open
        for longer than the spawned command.

        :arg args: is the command to run
            * If args is a list, the command will be run with shell=False.
            * If args is a string and use_unsafe_shell=False it will split args to a list and run with shell=False
            * If args is a string and use_unsafe_shell=True it runs with shell=True.
        :kw check_rc: Whether to call fail_json in case of non zero RC.
            Default False
        :kw close_fds: See documentation for subprocess.Popen(). Default True
        :kw executable: See documentation for subprocess.Popen(). Default None
        :kw data: If given, information to write to the stdin of the command
        :kw binary_data: If False, append a newline to the data.  Default False
        :kw path_prefix: If given, additional path to find the command in.
            This adds to the PATH environment variable so helper commands in
            the same directory can also be found
        :kw cwd: If given, working directory to run the command inside
        :kw use_unsafe_shell: See `args` parameter.  Default False
        :kw prompt_regex: Regex string (not a compiled regex) which can be
            used to detect prompts in the stdout which would otherwise cause
            the execution to hang (especially if no input data is specified)
        :kw environ_update: dictionary to *update* environ variables with
        :kw umask: Umask to be used when running the command. Default None
        :kw encoding: Since we return strings, we need to
            know the encoding to use to transform from bytes to text.  If you
            want to always get bytes back, use encoding=None.  The default is
            "utf-8".  This does not affect transformation of strings given as
            args.
        :kw errors: Since we return strings, we need to
            transform stdout and stderr from bytes to text.  If the bytes are
            undecodable in the ``encoding`` specified, then use this error
            handler to deal with them.  The default is ``surrogate_or_strict``
            which means that the bytes will be decoded using the
            surrogateescape error handler if available (available on all
            Python versions we support) otherwise a UnicodeError traceback
            will be raised.  This does not affect transformations of strings
            given as args.
        :kw expand_user_and_vars: When ``use_unsafe_shell=False`` this argument
            dictates whether ``~`` is expanded in paths and environment variables
            are expanded before running the command. When ``True`` a string such as
            ``$SHELL`` will be expanded regardless of escaping. When ``False`` and
            ``use_unsafe_shell=False`` no path or variable expansion will be done.
        :kw pass_fds: This argument dictates which file descriptors should be passed
            to an underlying ``Popen`` constructor.
        :kw before_communicate_callback: This function will be called
            after ``Popen`` object will be created
            but before communicating to the process.
            (``Popen`` object will be passed to callback as a first argument)
        :kw ignore_invalid_cwd: This flag indicates whether an invalid ``cwd``
            (non-existent or not a directory) should be ignored or should raise
            an exception.
        :kw handle_exceptions: This flag indicates whether an exception will
            be handled inline and issue a failed_json or if the caller should
            handle it.
        :returns: A 3-tuple of return code (int), stdout (str), and stderr (str).
            stdout and stderr are text strings converted according to the encoding
            and errors parameters.  If you want byte strings, use encoding=None
            to turn decoding to text off.
        """
        # used by clean args later on
        self._clean = None

        if not isinstance(args, (list, bytes, str)):
            msg = "Argument 'args' to run_command must be list or string"
            self.fail_json(rc=257, cmd=args, msg=msg)

        shell = False
        if use_unsafe_shell:

            # stringify args for unsafe/direct shell usage
            if isinstance(args, list):
                args = b" ".join([to_bytes(shlex.quote(x), errors='surrogate_or_strict') for x in args])
            else:
                args = to_bytes(args, errors='surrogate_or_strict')

            # not set explicitly, check if set by controller
            if executable:
                executable = to_bytes(executable, errors='surrogate_or_strict')
                args = [executable, b'-c', args]
            elif self._shell not in (None, '/bin/sh'):
                args = [to_bytes(self._shell, errors='surrogate_or_strict'), b'-c', args]
            else:
                shell = True
        else:
            # ensure args are a list
            if isinstance(args, (bytes, str)):
                try:
                    args = shlex.split(to_text(args, errors='surrogateescape'))
                except ValueError as e:
                    self.fail_json(msg="Invalid command syntax in run_command", exception=e)

            # expand ``~`` in paths, and all environment vars
            if expand_user_and_vars:
                args = [to_bytes(os.path.expanduser(os.path.expandvars(x)), errors='surrogate_or_strict') for x in args if x is not None]
            else:
                args = [to_bytes(x, errors='surrogate_or_strict') for x in args if x is not None]

        prompt_re = None
        if prompt_regex:
            if isinstance(prompt_regex, str):
                prompt_regex = to_bytes(prompt_regex, errors='surrogateescape')
            try:
                prompt_re = re.compile(prompt_regex, re.MULTILINE)
            except re.error:
                self.fail_json(msg="invalid prompt regular expression given to run_command")

        rc = 0
        msg = None
        st_in = None

        env = os.environ.copy()
        # We can set this from both an attribute and per call
        env.update(self.run_command_environ_update or {})
        env.update(environ_update or {})
        if path_prefix:
            path = env.get('PATH', '')
            if path:
                env['PATH'] = "%s:%s" % (path_prefix, path)
            else:
                env['PATH'] = path_prefix

        # If using test-module.py and explode, the remote lib path will resemble:
        #   /tmp/test_module_scratch/debug_dir/ansible/module_utils/basic.py
        # If using ansible or ansible-playbook with a remote system:
        #   /tmp/ansible_vmweLQ/ansible_modlib.zip/ansible/module_utils/basic.py

        # Clean out python paths set by ansiballz
        if 'PYTHONPATH' in env:
            pypaths = [x for x in env['PYTHONPATH'].split(':')
                       if x and
                       not x.endswith('/ansible_modlib.zip') and
                       not x.endswith('/debug_dir')]
            if pypaths and any(pypaths):
                env['PYTHONPATH'] = ':'.join(pypaths)

        if data:
            st_in = subprocess.PIPE

        def preexec():
            if umask:
                os.umask(umask)

        kwargs = dict(
            executable=executable,
            shell=shell,
            close_fds=close_fds,
            stdin=st_in,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=preexec,
            env=env,
        )
        if pass_fds:
            kwargs["pass_fds"] = pass_fds

        # make sure we're in the right working directory
        if cwd:
            cwd = to_bytes(os.path.abspath(os.path.expanduser(cwd)), errors='surrogate_or_strict')
            if os.path.isdir(cwd):
                kwargs['cwd'] = cwd
            elif not ignore_invalid_cwd:
                self.fail_json(msg="Provided cwd is not a valid directory: %s" % cwd)

        try:
            if self._debug:
                self.log('Executing: ' + self._clean_args(args))
            cmd = subprocess.Popen(args, **kwargs)
            if before_communicate_callback:
                before_communicate_callback(cmd)

            stdout = b''
            stderr = b''

            # Mirror the CPython subprocess logic and preference for the selector to use.
            # poll/select have the advantage of not requiring any extra file
            # descriptor, contrarily to epoll/kqueue (also, they require a single
            # syscall).
            if hasattr(selectors, 'PollSelector'):
                selector = selectors.PollSelector()
            else:
                selector = selectors.SelectSelector()

            if data:
                if not binary_data:
                    data += '\n'
                if isinstance(data, str):
                    data = to_bytes(data)

            selector.register(cmd.stdout, selectors.EVENT_READ)
            selector.register(cmd.stderr, selectors.EVENT_READ)

            if os.name == 'posix':
                fcntl.fcntl(cmd.stdout.fileno(), fcntl.F_SETFL, fcntl.fcntl(cmd.stdout.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK)
                fcntl.fcntl(cmd.stderr.fileno(), fcntl.F_SETFL, fcntl.fcntl(cmd.stderr.fileno(), fcntl.F_GETFL) | os.O_NONBLOCK)

            if data:
                cmd.stdin.write(data)
                cmd.stdin.close()

            while True:
                # A timeout of 1 is both a little short and a little long.
                # With None we could deadlock, with a lower value we would
                # waste cycles. As it is, this is a mild inconvenience if
                # we need to exit, and likely doesn't waste too many cycles
                events = selector.select(1)
                stdout_changed = False
                for key, event in events:
                    b_chunk = key.fileobj.read(32768)
                    if not b_chunk and b_chunk is not None:
                        selector.unregister(key.fileobj)
                    elif key.fileobj == cmd.stdout:
                        stdout += b_chunk
                        stdout_changed = True
                    elif key.fileobj == cmd.stderr:
                        stderr += b_chunk

                # if we're checking for prompts, do it now, but only if stdout
                # actually changed since the last loop
                if prompt_re and stdout_changed and prompt_re.search(stdout) and not data:
                    if encoding:
                        stdout = to_native(stdout, encoding=encoding, errors=errors)
                    return (257, stdout, "A prompt was encountered while running a command, but no input data was specified")

                # break out if no pipes are left to read or the pipes are completely read
                # and the process is terminated
                if (not events or not selector.get_map()) and cmd.poll() is not None:
                    break

                # No pipes are left to read but process is not yet terminated
                # Only then it is safe to wait for the process to be finished
                # NOTE: Actually cmd.poll() is always None here if no selectors are left
                elif not selector.get_map() and cmd.poll() is None:
                    cmd.wait()
                    # The process is terminated. Since no pipes to read from are
                    # left, there is no need to call select() again.
                    break

            cmd.stdout.close()
            cmd.stderr.close()
            selector.close()

            rc = cmd.returncode
        except OSError as ex:
            if handle_exceptions:
                self.fail_json(rc=ex.errno, stdout='', stderr='', msg="Error executing command.", cmd=self._clean_args(args), exception=ex)
            else:
                raise
        except Exception as ex:
            if handle_exceptions:
                self.fail_json(rc=257, stdout='', stderr='', msg="Error executing command.", cmd=self._clean_args(args), exception=ex)
            else:
                raise

        if rc != 0 and check_rc:
            msg = heuristic_log_sanitize(stderr.rstrip(), self.no_log_values)
            self.fail_json(cmd=self._clean_args(args), rc=rc, stdout=stdout, stderr=stderr, msg=msg)

        if encoding is not None:
            return (rc, to_native(stdout, encoding=encoding, errors=errors),
                    to_native(stderr, encoding=encoding, errors=errors))

        return (rc, stdout, stderr)