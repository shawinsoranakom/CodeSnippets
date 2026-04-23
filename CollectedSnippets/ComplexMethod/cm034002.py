def exec_command(self, cmd: str, in_data: bytes | None = None, sudoable: bool = True) -> tuple[int, bytes, bytes]:
        """ run a command on the local host """

        super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

        display.debug("in local.exec_command()")

        executable = C.DEFAULT_EXECUTABLE.split()[0] if C.DEFAULT_EXECUTABLE else None

        if not os.path.exists(to_bytes(executable, errors='surrogate_or_strict')):
            raise AnsibleError("failed to find the executable specified %s."
                               " Please verify if the executable exists and re-try." % executable)

        display.vvv(u"EXEC {0}".format(to_text(cmd)), host=self._play_context.remote_addr)
        display.debug("opening command with Popen()")

        if isinstance(cmd, (str, bytes)):
            cmd = to_text(cmd)
        else:
            cmd = map(to_text, cmd)

        pty_primary = None
        stdin = subprocess.PIPE
        if sudoable and self.become and self.become.expect_prompt() and not self.get_option('pipelining'):
            # Create a pty if sudoable for privilege escalation that needs it.
            # Falls back to using a standard pipe if this fails, which may
            # cause the command to fail in certain situations where we are escalating
            # privileges or the command otherwise needs a pty.
            try:
                pty_primary, stdin = pty.openpty()
            except OSError as ex:
                display.debug(f"Unable to open pty: {ex}")

        p = subprocess.Popen(
            cmd,
            shell=isinstance(cmd, (str, bytes)),
            executable=executable,
            cwd=self.cwd,
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # if we created a pty, we can close the other half of the pty now, otherwise primary is stdin
        if pty_primary is not None:
            os.close(stdin)

        display.debug("done running command with Popen()")

        become_stdout_bytes, become_stderr_bytes = self._ensure_become_success(p, pty_primary, sudoable)

        display.debug("getting output with communicate()")
        stdout, stderr = p.communicate(in_data)
        display.debug("done communicating")

        # preserve output from privilege escalation stage as `bytes`; it may contain actual output (eg `raw`) or error messages
        stdout = become_stdout_bytes + stdout
        stderr = become_stderr_bytes + stderr

        # finally, close the other half of the pty, if it was created
        if pty_primary:
            os.close(pty_primary)

        display.debug("done with local.exec_command()")
        return p.returncode, stdout, stderr