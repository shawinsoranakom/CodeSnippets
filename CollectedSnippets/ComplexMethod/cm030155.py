def interaction(self, frame, tb_or_exc):
        # Restore the previous signal handler at the Pdb prompt.
        if Pdb._previous_sigint_handler:
            try:
                signal.signal(signal.SIGINT, Pdb._previous_sigint_handler)
            except ValueError:  # ValueError: signal only works in main thread
                pass
            else:
                Pdb._previous_sigint_handler = None

        self._current_task = self._get_asyncio_task()

        _chained_exceptions, tb = self._get_tb_and_exceptions(tb_or_exc)
        if isinstance(tb_or_exc, BaseException):
            assert tb is not None, "main exception must have a traceback"
        with self._hold_exceptions(_chained_exceptions):
            self.setup(frame, tb)
            # We should print the stack entry if and only if the user input
            # is expected, and we should print it right before the user input.
            # We achieve this by appending _pdbcmd_print_frame_status to the
            # command queue. If cmdqueue is not exhausted, the user input is
            # not expected and we will not print the stack entry.
            self.cmdqueue.append('_pdbcmd_print_frame_status')
            self._cmdloop()
            # If _pdbcmd_print_frame_status is not used, pop it out
            if self.cmdqueue and self.cmdqueue[-1] == '_pdbcmd_print_frame_status':
                self.cmdqueue.pop()
            self.forget()