def _pop(self, timeout, default=('', None)):
        # Get the next response, or a default value on timeout.
        # The timeout arg can be an int or float, or None for no timeout.
        # Timeouts require a socket connection (not IMAP4_stream).
        # This method ignores self._duration.

        # Historical Note:
        # The timeout was originally implemented using select() after
        # checking for the presence of already-buffered data.
        # That allowed timeouts on pipe connetions like IMAP4_stream.
        # However, it seemed possible that SSL data arriving without any
        # IMAP data afterward could cause select() to indicate available
        # application data when there was none, leading to a read() call
        # that would block with no timeout. It was unclear under what
        # conditions this would happen in practice. Our implementation was
        # changed to use socket timeouts instead of select(), just to be
        # safe.

        imap = self._imap
        if imap.state != 'IDLING':
            raise imap.error('_pop() only works during IDLE')

        if imap._idle_responses:
            # Response is ready to return to the user
            resp = imap._idle_responses.pop(0)
            if __debug__ and imap.debug >= 4:
                imap._mesg(f'idle _pop({timeout}) de-queued {resp[0]}')
            return resp

        if __debug__ and imap.debug >= 4:
            imap._mesg(f'idle _pop({timeout}) reading')

        if timeout is not None:
            if timeout <= 0:
                return default
            timeout = float(timeout)  # Required by socket.settimeout()

        try:
            imap._get_response(timeout)  # Reads line, calls _append_untagged()
        except IMAP4._responsetimeout:
            if __debug__ and imap.debug >= 4:
                imap._mesg(f'idle _pop({timeout}) done')
            return default

        resp = imap._idle_responses.pop(0)

        if __debug__ and imap.debug >= 4:
            imap._mesg(f'idle _pop({timeout}) read {resp[0]}')
        return resp