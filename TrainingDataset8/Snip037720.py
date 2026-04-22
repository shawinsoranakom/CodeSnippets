def _on_scriptrunner_event(
        self,
        sender: Optional[ScriptRunner],
        event: ScriptRunnerEvent,
        forward_msg: Optional[ForwardMsg] = None,
        exception: Optional[BaseException] = None,
        client_state: Optional[ClientState] = None,
        page_script_hash: Optional[str] = None,
    ) -> None:
        """Called when our ScriptRunner emits an event.

        This is generally called from the sender ScriptRunner's script thread.
        We forward the event on to _handle_scriptrunner_event_on_event_loop,
        which will be called on the main thread.
        """
        self._event_loop.call_soon_threadsafe(
            lambda: self._handle_scriptrunner_event_on_event_loop(
                sender, event, forward_msg, exception, client_state, page_script_hash
            )
        )