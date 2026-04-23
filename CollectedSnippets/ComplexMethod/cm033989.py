def _winrm_exec(
        self,
        command: str,
        args: t.Iterable[bytes | str] = (),
        from_exec: bool = False,
        stdin_iterator: t.Iterable[tuple[bytes, bool]] = None,
    ) -> tuple[int, bytes, bytes]:
        if not self.protocol:
            self.protocol = self._winrm_connect()
            self._connected = True
        if from_exec:
            display.vvvvv("WINRM EXEC %r %r" % (command, args), host=self._winrm_host)
        else:
            display.vvvvvv("WINRM EXEC %r %r" % (command, args), host=self._winrm_host)
        command_id = None
        try:
            stdin_push_failed = False
            command_id = self._winrm_run_command(
                to_bytes(command),
                tuple(map(to_bytes, args)),
                console_mode_stdin=(stdin_iterator is None),
            )

            try:
                if stdin_iterator:
                    self._winrm_write_stdin(command_id, stdin_iterator)

            except Exception as ex:
                display.error_as_warning(f"ERROR DURING WINRM SEND INPUT TO {self._winrm_host}. Attempting to recover.", ex)
                stdin_push_failed = True

            # Even on a failure above we try at least once to get the output
            # in case the stdin was actually written and it an normally.
            b_stdout, b_stderr, rc = self._winrm_get_command_output(
                self.protocol,
                self.shell_id,
                command_id,
                try_once=stdin_push_failed,
            )
            stdout = to_text(b_stdout)
            stderr = to_text(b_stderr)

            if from_exec:
                display.vvvvv('WINRM RESULT <Response code %d, out %r, err %r>' % (rc, stdout, stderr), host=self._winrm_host)
            display.vvvvvv('WINRM RC %d' % rc, host=self._winrm_host)
            display.vvvvvv('WINRM STDOUT %s' % stdout, host=self._winrm_host)
            display.vvvvvv('WINRM STDERR %s' % stderr, host=self._winrm_host)

            # This is done after logging so we can still see the raw stderr for
            # debugging purposes.
            b_stderr = _clixml.replace_stderr_clixml(b_stderr)
            stderr = to_text(stderr)

            if stdin_push_failed:
                # There are cases where the stdin input failed but the WinRM service still processed it. We attempt to
                # see if stdout contains a valid json return value so we can ignore this error
                try:
                    filtered_output, dummy = _filter_non_json_lines(stdout)
                    json.loads(filtered_output)
                except ValueError:
                    # stdout does not contain a return response, stdin input was a fatal error
                    raise AnsibleError(f'winrm send_input failed; \nstdout: {stdout}\nstderr {stderr}')

            return rc, b_stdout, b_stderr
        except requests.exceptions.Timeout as exc:
            raise AnsibleConnectionFailure('winrm connection error: %s' % to_native(exc))
        finally:
            if command_id:
                # Due to a bug in how pywinrm works with message encryption we
                # ignore a 400 error which can occur when a task timeout is
                # set and the code tries to clean up the command. This happens
                # as the cleanup msg is sent over a new socket but still uses
                # the already encrypted payload bound to the other socket
                # causing the server to reply with 400 Bad Request.
                try:
                    self.protocol.cleanup_command(self.shell_id, command_id)
                except WinRMTransportError as e:
                    if e.code != 400:
                        raise

                    display.warning("Failed to cleanup running WinRM command, resources might still be in use on the target server")