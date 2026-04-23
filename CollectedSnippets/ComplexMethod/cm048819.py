def _handle_transport_error(self, exc):
        """
        Find out which close code should be sent according to given
        exception and call `self._disconnect` in order to close the
        connection cleanly.
        """
        code, reason = CloseCode.SERVER_ERROR, str(exc)
        if isinstance(exc, (ConnectionClosed, OSError)):
            code = CloseCode.ABNORMAL_CLOSURE
        elif isinstance(exc, (ProtocolError, InvalidCloseCodeException)):
            code = CloseCode.PROTOCOL_ERROR
        elif isinstance(exc, UnicodeDecodeError):
            code = CloseCode.INCONSISTENT_DATA
        elif isinstance(exc, PayloadTooLargeException):
            code = CloseCode.MESSAGE_TOO_BIG
        elif isinstance(exc, (PoolError, RateLimitExceededException)):
            code = CloseCode.TRY_LATER
        elif isinstance(exc, SessionExpiredException):
            code = CloseCode.SESSION_EXPIRED
        if code is CloseCode.SERVER_ERROR:
            reason = None
            registry = Registry(self._session.db)
            sequence = registry.registry_sequence
            registry = registry.check_signaling()
            if sequence != registry.registry_sequence:
                _logger.warning("Bus operation aborted; registry has been reloaded")
            else:
                _logger.error(exc, exc_info=True)
        if self.state is ConnectionState.OPEN:
            self._disconnect(code, reason)
        else:
            self._terminate()