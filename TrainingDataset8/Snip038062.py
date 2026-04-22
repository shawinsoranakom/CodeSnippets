def request_stop(self) -> None:
        """Request that the ScriptRunner stop running its script and
        shut down. The ScriptRunner will handle this request when it reaches
        an interrupt point.

        Safe to call from any thread.
        """
        self._requests.request_stop()

        # "Disconnect" our SafeSessionState wrapper from its underlying
        # SessionState instance. This will cause all further session_state
        # operations in this ScriptRunner to no-op.
        #
        # After `request_stop` is called, our script will continue executing
        # until it reaches a yield point. AppSession may also *immediately*
        # spin up a new ScriptRunner after this call, which means we'll
        # potentially have two active ScriptRunners for a brief period while
        # this one is shutting down. Disconnecting our SessionState ensures
        # that this ScriptRunner's thread won't introduce SessionState-
        # related race conditions during this script overlap.
        self._session_state.disconnect()