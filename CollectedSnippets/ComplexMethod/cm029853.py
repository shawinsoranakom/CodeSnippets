def __enter__(self):
        imap = self._imap
        assert not imap._idle_responses
        assert not imap._idle_capture

        if __debug__ and imap.debug >= 4:
            imap._mesg(f'idle start duration={self._duration}')

        # Start capturing untagged responses before sending IDLE,
        # so we can deliver via iteration any that arrive while
        # the IDLE command continuation request is still pending.
        imap._idle_capture = True

        try:
            self._tag = imap._command('IDLE')
            # As with any command, the server is allowed to send us unrelated,
            # untagged responses before acting on IDLE.  These lines will be
            # returned by _get_response().  When the server is ready, it will
            # send an IDLE continuation request, indicated by _get_response()
            # returning None.  We therefore process responses in a loop until
            # this occurs.
            while resp := imap._get_response():
                if imap.tagged_commands[self._tag]:
                    typ, data = imap.tagged_commands.pop(self._tag)
                    if typ == 'NO':
                        raise imap.error(f'idle denied: {data}')
                    raise imap.abort(f'unexpected status response: {resp}')

            if __debug__ and imap.debug >= 4:
                prompt = imap.continuation_response
                imap._mesg(f'idle continuation prompt: {prompt}')
        except BaseException:
            imap._idle_capture = False
            raise

        if self._duration is not None:
            self._deadline = time.monotonic() + self._duration

        self._saved_state = imap.state
        imap.state = 'IDLING'

        return self