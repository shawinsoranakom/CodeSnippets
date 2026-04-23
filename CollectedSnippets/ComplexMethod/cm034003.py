def _ensure_become_success(self, p: subprocess.Popen, pty_primary: int, sudoable: bool) -> tuple[bytes, bytes]:
        """
        Ensure that become succeeds, returning a tuple containing stdout captured after success and all stderr.
        Returns immediately if `self.become` or `sudoable` are False, or `build_become_command` was not called, without performing any additional checks.
        """
        if not self.become or not sudoable or not self.become._id:  # _id is set by build_become_command, if it was not called, assume no become
            return b'', b''

        start_seconds = time.monotonic()
        become_stdout = bytearray()
        become_stderr = bytearray()
        last_stdout_prompt_offset = 0
        last_stderr_prompt_offset = 0

        # map the buffers to their associated stream for the selector reads
        become_capture = {
            p.stdout: become_stdout,
            p.stderr: become_stderr,
        }

        expect_password_prompt = self.become.expect_prompt()
        sent_password = False

        def become_error_msg(reason: str) -> str:
            error_message = f'{reason} waiting for become success'

            if expect_password_prompt and not sent_password:
                error_message += ' or become password prompt'

            error_message += '.'

            if become_stdout:
                error_message += f'\n>>> Standard Output\n{to_text(bytes(become_stdout))}'

            if become_stderr:
                error_message += f'\n>>> Standard Error\n{to_text(bytes(become_stderr))}'

            return error_message

        os.set_blocking(p.stdout.fileno(), False)
        os.set_blocking(p.stderr.fileno(), False)

        with selectors.DefaultSelector() as selector:
            selector.register(p.stdout, selectors.EVENT_READ, 'stdout')
            selector.register(p.stderr, selectors.EVENT_READ, 'stderr')

            while not self.become.check_success(become_stdout):
                if not selector.get_map():  # we only reach end of stream after all descriptors are EOF
                    raise AnsibleError(become_error_msg('Premature end of stream'))

                if expect_password_prompt and (
                    self.become.check_password_prompt(bytes(become_stdout[last_stdout_prompt_offset:])) or
                    self.become.check_password_prompt(bytes(become_stderr[last_stderr_prompt_offset:]))
                ):
                    if sent_password:
                        raise AnsibleError(become_error_msg('Duplicate become password prompt encountered'))

                    last_stdout_prompt_offset = len(become_stdout)
                    last_stderr_prompt_offset = len(become_stderr)

                    password_to_send = to_bytes(self.become.get_option('become_pass') or '') + b'\n'

                    if pty_primary is None:
                        p.stdin.write(password_to_send)
                        p.stdin.flush()
                    else:
                        os.write(pty_primary, password_to_send)

                    sent_password = True

                remaining_timeout_seconds = self._become_success_timeout - (time.monotonic() - start_seconds)
                events = selector.select(remaining_timeout_seconds) if remaining_timeout_seconds > 0 else []

                if not events:
                    # ignoring remaining output after timeout to prevent hanging
                    raise AnsibleConnectionFailure(become_error_msg('Timed out'))

                # read all content (non-blocking) from streams that signaled available input and append to the associated buffer
                for key, event in events:
                    obj = t.cast(t.BinaryIO, key.fileobj)

                    if chunk := obj.read():
                        become_capture[obj] += chunk
                    else:
                        selector.unregister(obj)  # EOF on this obj, stop polling it

        os.set_blocking(p.stdout.fileno(), True)
        os.set_blocking(p.stderr.fileno(), True)

        become_stdout_bytes = bytes(become_stdout)
        become_stderr_bytes = bytes(become_stderr)

        if self.get_option('become_strip_preamble'):
            become_stdout_bytes = self.become.strip_become_success(self.become.strip_become_prompt(become_stdout_bytes))
            become_stderr_bytes = self.become.strip_become_prompt(become_stderr_bytes)

        return become_stdout_bytes, become_stderr_bytes