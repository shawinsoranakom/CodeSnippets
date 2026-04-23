def eof_received(self):
        """Called when the other end of the low-level stream
        is half-closed.

        If this returns a false value (including None), the transport
        will close itself.  If it returns a true value, closing the
        transport is up to the protocol.
        """
        self._eof_received = True
        try:
            if self._loop.get_debug():
                logger.debug("%r received EOF", self)

            if self._state == SSLProtocolState.DO_HANDSHAKE:
                self._on_handshake_complete(ConnectionResetError)

            elif self._state == SSLProtocolState.WRAPPED:
                self._set_state(SSLProtocolState.FLUSHING)
                if self._app_reading_paused:
                    return True
                else:
                    self._do_flush()

            elif self._state == SSLProtocolState.FLUSHING:
                self._do_write()
                self._set_state(SSLProtocolState.SHUTDOWN)
                self._do_shutdown()

            elif self._state == SSLProtocolState.SHUTDOWN:
                self._do_shutdown()

        except Exception:
            self._transport.close()
            raise