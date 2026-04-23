def display(
        self,
        msg: str,
        color: str | None = None,
        stderr: bool = False,
        screen_only: bool = False,
        log_only: bool = False,
        newline: bool = True,
        caplevel: int | None = None,
    ) -> None:
        """ Display a message to the user

        Note: msg *must* be a unicode string to prevent UnicodeError tracebacks.
        """

        if not isinstance(msg, str):
            raise TypeError(f'Display message must be str, not: {msg.__class__.__name__}')

        # Convert Windows newlines to Unix newlines.
        # Some environments, such as Azure Pipelines, render `\r` as an additional `\n`.
        msg = msg.replace('\r\n', '\n')

        nocolor = msg

        if not log_only:

            has_newline = msg.endswith(u'\n')
            if has_newline:
                msg2 = msg[:-1]
            else:
                msg2 = msg

            if color:
                msg2 = stringc(msg2, color)

            if has_newline or newline:
                msg2 = msg2 + u'\n'

            # Note: After Display() class is refactored need to update the log capture
            # code in 'cli/scripts/ansible_connection_cli_stub.py' (and other relevant places).
            if not stderr:
                fileobj = sys.stdout
            else:
                fileobj = sys.stderr

            with self._lock:
                fileobj.write(msg2)

            # With locks, and the fact that we aren't printing from forks
            # just write, and let the system flush. Everything should come out peachy
            # I've left this code for historical purposes, or in case we need to add this
            # back at a later date. For now ``TaskQueueManager.cleanup`` will perform a
            # final flush at shutdown.
            # try:
            #     fileobj.flush()
            # except OSError as e:
            #     # Ignore EPIPE in case fileobj has been prematurely closed, eg.
            #     # when piping to "head -n1"
            #     if e.errno != errno.EPIPE:
            #         raise

        if logger and not screen_only:
            self._log(nocolor, color, caplevel)