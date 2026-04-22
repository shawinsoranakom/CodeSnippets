def _enqueue_forward_msg(self, msg: ForwardMsg) -> None:
        """Enqueue a ForwardMsg to our browser queue.
        This private function is called by ScriptRunContext only.

        It may be called from the script thread OR the main thread.
        """
        # Whenever we enqueue a ForwardMsg, we also handle any pending
        # execution control request. This means that a script can be
        # cleanly interrupted and stopped inside most `st.foo` calls.
        #
        # (If "runner.installTracer" is true, then we'll actually be
        # handling these requests in a callback called after every Python
        # instruction instead.)
        if not config.get_option("runner.installTracer"):
            self._maybe_handle_execution_control_request()

        # Pass the message to our associated AppSession.
        self.on_event.send(
            self, event=ScriptRunnerEvent.ENQUEUE_FORWARD_MSG, forward_msg=msg
        )