def _set_state(self, new_state):
        allowed = False

        if new_state == SSLProtocolState.UNWRAPPED:
            allowed = True

        elif (
            self._state == SSLProtocolState.UNWRAPPED and
            new_state == SSLProtocolState.DO_HANDSHAKE
        ):
            allowed = True

        elif (
            self._state == SSLProtocolState.DO_HANDSHAKE and
            new_state == SSLProtocolState.WRAPPED
        ):
            allowed = True

        elif (
            self._state == SSLProtocolState.WRAPPED and
            new_state == SSLProtocolState.FLUSHING
        ):
            allowed = True

        elif (
            self._state == SSLProtocolState.FLUSHING and
            new_state == SSLProtocolState.SHUTDOWN
        ):
            allowed = True

        if allowed:
            self._state = new_state

        else:
            raise RuntimeError(
                'cannot switch state from {} to {}'.format(
                    self._state, new_state))