def _low_level_execute_command(
        self,
        cmd: str,
        sudoable: bool = True,
        in_data: bytes | None = None,
        executable: str | None = None,
        encoding_errors: str = 'surrogate_then_replace',
        chdir: str | None = None,
        process_result: Callable[[int, bytes, bytes], tuple[int, bytes, bytes]] | None = None,
    ) -> LowLevelExecuteCommandResult:
        """
        This is the function which executes the low level shell command, which
        may be commands to create/remove directories for temporary files, or to
        run the module code or python directly when pipelining.

        :kwarg encoding_errors: If the value returned by the command isn't
            utf-8 then we have to figure out how to transform it to unicode.
            If the value is just going to be displayed to the user (or
            discarded) then the default of 'replace' is fine.  If the data is
            used as a key or is going to be written back out to a file
            verbatim, then this won't work.  May have to use some sort of
            replacement strategy (python3 could use surrogateescape)
        :kwarg chdir: cd into this directory before executing the command.
        """

        display.debug("_low_level_execute_command(): starting")
        # if not cmd:
        #     # this can happen with powershell modules when there is no analog to a Windows command (like chmod)
        #     display.debug("_low_level_execute_command(): no command, exiting")
        #     return dict(stdout='', stderr='', rc=254)

        if chdir:
            display.debug("_low_level_execute_command(): changing cwd to %s for this command" % chdir)
            cmd = self._connection._shell.append_command('cd %s' % chdir, cmd)

        # https://github.com/ansible/ansible/issues/68054
        if executable:
            self._connection._shell.executable = executable

        ruser = self._get_remote_user()
        buser = self.get_become_option('become_user')
        if (sudoable and self._connection.become and  # if sudoable and have become
                resource_from_fqcr(self._connection.transport) != 'network_cli' and  # if not using network_cli
                (C.BECOME_ALLOW_SAME_USER or (buser != ruser or not any((ruser, buser))))):  # if we allow same user PE or users are different and either is set
            display.debug("_low_level_execute_command(): using become for this command")
            cmd = self._connection.become.build_become_command(cmd, self._connection._shell)

        if self._connection.allow_executable:
            if executable is None:
                executable = self._play_context.executable
            if executable:
                cmd = executable + ' -c ' + shlex.quote(cmd)

        display.debug("_low_level_execute_command(): executing: %s" % (cmd,))

        # Change directory to basedir of task for command execution when connection is local
        if self._connection.transport == 'local':
            self._connection.cwd = self._loader.get_basedir()

        rc, stdout, stderr = self._connection.exec_command(cmd, in_data=in_data, sudoable=sudoable)

        if process_result:
            rc, stdout, stderr = process_result(rc, stdout, stderr)

        # stdout and stderr may be either a file-like or a bytes object.
        # Convert either one to a text type
        if isinstance(stdout, bytes):
            out = to_text(stdout, errors=encoding_errors)
        elif not isinstance(stdout, str):
            out = to_text(b''.join(stdout.readlines()), errors=encoding_errors)
        else:
            out = stdout

        if isinstance(stderr, bytes):
            err = to_text(stderr, errors=encoding_errors)
        elif not isinstance(stderr, str):
            err = to_text(b''.join(stderr.readlines()), errors=encoding_errors)
        else:
            err = stderr

        if rc is None:
            rc = 0

        # be sure to remove the BECOME-SUCCESS message now
        out = self._strip_success_message(out)

        display.debug(u"_low_level_execute_command() done: rc=%d, stdout=%s, stderr=%s" % (rc, out, err))
        return dict(rc=rc, stdout=out, stdout_lines=out.splitlines(), stderr=err, stderr_lines=err.splitlines())