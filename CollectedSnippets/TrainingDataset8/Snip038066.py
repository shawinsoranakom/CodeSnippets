def _run_script_thread(self) -> None:
        """The entry point for the script thread.

        Processes the ScriptRequestQueue, which will at least contain the RERUN
        request that will trigger the first script-run.

        When the ScriptRequestQueue is empty, or when a SHUTDOWN request is
        dequeued, this function will exit and its thread will terminate.
        """
        assert self._is_in_script_thread()

        _LOGGER.debug("Beginning script thread")

        # Create and attach the thread's ScriptRunContext
        ctx = ScriptRunContext(
            session_id=self._session_id,
            _enqueue=self._enqueue_forward_msg,
            query_string=self._client_state.query_string,
            session_state=self._session_state,
            uploaded_file_mgr=self._uploaded_file_mgr,
            page_script_hash=self._client_state.page_script_hash,
            user_info=self._user_info,
            gather_usage_stats=bool(config.get_option("browser.gatherUsageStats")),
        )
        add_script_run_ctx(threading.current_thread(), ctx)

        request = self._requests.on_scriptrunner_ready()
        while request.type == ScriptRequestType.RERUN:
            # When the script thread starts, we'll have a pending rerun
            # request that we'll handle immediately. When the script finishes,
            # it's possible that another request has come in that we need to
            # handle, which is why we call _run_script in a loop.
            self._run_script(request.rerun_data)
            request = self._requests.on_scriptrunner_ready()

        assert request.type == ScriptRequestType.STOP

        # Send a SHUTDOWN event before exiting. This includes the widget values
        # as they existed after our last successful script run, which the
        # AppSession will pass on to the next ScriptRunner that gets
        # created.
        client_state = ClientState()
        client_state.query_string = ctx.query_string
        client_state.page_script_hash = ctx.page_script_hash
        widget_states = self._session_state.get_widget_states()
        client_state.widget_states.widgets.extend(widget_states)
        self.on_event.send(
            self, event=ScriptRunnerEvent.SHUTDOWN, client_state=client_state
        )