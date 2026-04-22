def _handle_scriptrunner_event_on_event_loop(
        self,
        sender: Optional[ScriptRunner],
        event: ScriptRunnerEvent,
        forward_msg: Optional[ForwardMsg] = None,
        exception: Optional[BaseException] = None,
        client_state: Optional[ClientState] = None,
        page_script_hash: Optional[str] = None,
    ) -> None:
        """Handle a ScriptRunner event.

        This function must only be called on our eventloop thread.

        Parameters
        ----------
        sender : ScriptRunner | None
            The ScriptRunner that emitted the event. (This may be set to
            None when called from `handle_backmsg_exception`, if no
            ScriptRunner was active when the backmsg exception was raised.)

        event : ScriptRunnerEvent
            The event type.

        forward_msg : ForwardMsg | None
            The ForwardMsg to send to the frontend. Set only for the
            ENQUEUE_FORWARD_MSG event.

        exception : BaseException | None
            An exception thrown during compilation. Set only for the
            SCRIPT_STOPPED_WITH_COMPILE_ERROR event.

        client_state : streamlit.proto.ClientState_pb2.ClientState | None
            The ScriptRunner's final ClientState. Set only for the
            SHUTDOWN event.

        page_script_hash : str | None
            A hash of the script path corresponding to the page currently being
            run. Set only for the SCRIPT_STARTED event.
        """

        assert (
            self._event_loop == asyncio.get_running_loop()
        ), "This function must only be called on the eventloop thread the AppSession was created on."

        if sender is not self._scriptrunner:
            # This event was sent by a non-current ScriptRunner; ignore it.
            # This can happen after sppinng up a new ScriptRunner (to handle a
            # rerun request, for example) while another ScriptRunner is still
            # shutting down. The shutting-down ScriptRunner may still
            # emit events.
            LOGGER.debug("Ignoring event from non-current ScriptRunner: %s", event)
            return

        prev_state = self._state

        if event == ScriptRunnerEvent.SCRIPT_STARTED:
            if self._state != AppSessionState.SHUTDOWN_REQUESTED:
                self._state = AppSessionState.APP_IS_RUNNING

            assert (
                page_script_hash is not None
            ), "page_script_hash must be set for the SCRIPT_STARTED event"

            self._clear_queue()
            self._enqueue_forward_msg(
                self._create_new_session_message(page_script_hash)
            )

        elif (
            event == ScriptRunnerEvent.SCRIPT_STOPPED_WITH_SUCCESS
            or event == ScriptRunnerEvent.SCRIPT_STOPPED_WITH_COMPILE_ERROR
        ):

            if self._state != AppSessionState.SHUTDOWN_REQUESTED:
                self._state = AppSessionState.APP_NOT_RUNNING

            script_succeeded = event == ScriptRunnerEvent.SCRIPT_STOPPED_WITH_SUCCESS

            script_finished_msg = self._create_script_finished_message(
                ForwardMsg.FINISHED_SUCCESSFULLY
                if script_succeeded
                else ForwardMsg.FINISHED_WITH_COMPILE_ERROR
            )
            self._enqueue_forward_msg(script_finished_msg)

            self._debug_last_backmsg_id = None

            if script_succeeded:
                # The script completed successfully: update our
                # LocalSourcesWatcher to account for any source code changes
                # that change which modules should be watched.
                self._local_sources_watcher.update_watched_modules()
            else:
                # The script didn't complete successfully: send the exception
                # to the frontend.
                assert (
                    exception is not None
                ), "exception must be set for the SCRIPT_STOPPED_WITH_COMPILE_ERROR event"
                msg = ForwardMsg()
                exception_utils.marshall(
                    msg.session_event.script_compilation_exception, exception
                )
                self._enqueue_forward_msg(msg)

        elif event == ScriptRunnerEvent.SCRIPT_STOPPED_FOR_RERUN:
            script_finished_msg = self._create_script_finished_message(
                ForwardMsg.FINISHED_EARLY_FOR_RERUN
            )
            self._enqueue_forward_msg(script_finished_msg)
            self._local_sources_watcher.update_watched_modules()

        elif event == ScriptRunnerEvent.SHUTDOWN:
            assert (
                client_state is not None
            ), "client_state must be set for the SHUTDOWN event"

            if self._state == AppSessionState.SHUTDOWN_REQUESTED:
                # Only clear media files if the script is done running AND the
                # session is actually shutting down.
                runtime.get_instance().media_file_mgr.clear_session_refs(self.id)

            self._client_state = client_state
            self._scriptrunner = None

        elif event == ScriptRunnerEvent.ENQUEUE_FORWARD_MSG:
            assert (
                forward_msg is not None
            ), "null forward_msg in ENQUEUE_FORWARD_MSG event"
            self._enqueue_forward_msg(forward_msg)

        # Send a message if our run state changed
        app_was_running = prev_state == AppSessionState.APP_IS_RUNNING
        app_is_running = self._state == AppSessionState.APP_IS_RUNNING
        if app_is_running != app_was_running:
            self._enqueue_forward_msg(self._create_session_state_changed_message())