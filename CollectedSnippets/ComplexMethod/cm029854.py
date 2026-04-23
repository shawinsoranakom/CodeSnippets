def __exit__(self, exc_type, exc_val, exc_tb):
        imap = self._imap

        if __debug__ and imap.debug >= 4:
            imap._mesg('idle done')
        imap.state = self._saved_state

        # Stop intercepting untagged responses before sending DONE,
        # since we can no longer deliver them via iteration.
        imap._idle_capture = False

        # If we captured untagged responses while the IDLE command
        # continuation request was still pending, but the user did not
        # iterate over them before exiting IDLE, we must put them
        # someplace where the user can retrieve them.  The only
        # sensible place for this is the untagged_responses dict,
        # despite its unfortunate inability to preserve the relative
        # order of different response types.
        if leftovers := len(imap._idle_responses):
            if __debug__ and imap.debug >= 4:
                imap._mesg(f'idle quit with {leftovers} leftover responses')
            while imap._idle_responses:
                typ, data = imap._idle_responses.pop(0)
                # Append one fragment at a time, just as _get_response() does
                for datum in data:
                    imap._append_untagged(typ, datum)

        try:
            imap.send(b'DONE' + CRLF)
            status, [msg] = imap._command_complete('IDLE', self._tag)
            if __debug__ and imap.debug >= 4:
                imap._mesg(f'idle status: {status} {msg!r}')
        except OSError:
            if not exc_type:
                raise

        return False