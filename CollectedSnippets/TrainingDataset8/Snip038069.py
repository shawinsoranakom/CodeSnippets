def _maybe_handle_execution_control_request(self) -> None:
        """Check our current ScriptRequestState to see if we have a
        pending STOP or RERUN request.

        This function is called every time the app script enqueues a
        ForwardMsg, which means that most `st.foo` commands - which generally
        involve sending a ForwardMsg to the frontend - act as implicit
        yield points in the script's execution.
        """
        if not self._is_in_script_thread():
            # We can only handle execution_control_request if we're on the
            # script execution thread. However, it's possible for deltas to
            # be enqueued (and, therefore, for this function to be called)
            # in separate threads, so we check for that here.
            return

        if not self._execing:
            # If the _execing flag is not set, we're not actually inside
            # an exec() call. This happens when our script exec() completes,
            # we change our state to STOPPED, and a statechange-listener
            # enqueues a new ForwardEvent
            return

        request = self._requests.on_scriptrunner_yield()
        if request is None:
            # No RERUN or STOP request.
            return

        if request.type == ScriptRequestType.RERUN:
            raise RerunException(request.rerun_data)

        assert request.type == ScriptRequestType.STOP
        raise StopException()