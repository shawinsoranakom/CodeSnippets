def handle_backmsg_exception(self, e: BaseException) -> None:
        """Handle an Exception raised while processing a BackMsg from the browser."""
        # This does a few things:
        # 1) Clears the current app in the browser.
        # 2) Marks the current app as "stopped" in the browser.
        # 3) HACK: Resets any script params that may have been broken (e.g. the
        # command-line when rerunning with wrong argv[0])

        self._on_scriptrunner_event(
            self._scriptrunner, ScriptRunnerEvent.SCRIPT_STOPPED_WITH_SUCCESS
        )
        self._on_scriptrunner_event(
            self._scriptrunner,
            ScriptRunnerEvent.SCRIPT_STARTED,
            page_script_hash="",
        )
        self._on_scriptrunner_event(
            self._scriptrunner, ScriptRunnerEvent.SCRIPT_STOPPED_WITH_SUCCESS
        )

        # Send an Exception message to the frontend.
        # Because _on_scriptrunner_event does its work in an eventloop callback,
        # this exception ForwardMsg *must* also be enqueued in a callback,
        # so that it will be enqueued *after* the various ForwardMsgs that
        # _on_scriptrunner_event sends.
        self._event_loop.call_soon_threadsafe(
            lambda: self._enqueue_forward_msg(self._create_exception_message(e))
        )