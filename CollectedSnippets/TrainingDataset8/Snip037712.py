def request_rerun(self, client_state: Optional[ClientState]) -> None:
        """Signal that we're interested in running the script.

        If the script is not already running, it will be started immediately.
        Otherwise, a rerun will be requested.

        Parameters
        ----------
        client_state : streamlit.proto.ClientState_pb2.ClientState | None
            The ClientState protobuf to run the script with, or None
            to use previous client state.

        """
        if self._state == AppSessionState.SHUTDOWN_REQUESTED:
            LOGGER.warning("Discarding rerun request after shutdown")
            return

        if client_state:
            rerun_data = RerunData(
                client_state.query_string,
                client_state.widget_states,
                client_state.page_script_hash,
                client_state.page_name,
            )
        else:
            rerun_data = RerunData()

        if self._scriptrunner is not None:
            if bool(config.get_option("runner.fastReruns")):
                # If fastReruns is enabled, we don't send rerun requests to our
                # existing ScriptRunner. Instead, we tell it to shut down. We'll
                # then spin up a new ScriptRunner, below, to handle the rerun
                # immediately.
                self._scriptrunner.request_stop()
                self._scriptrunner = None
            else:
                # fastReruns is not enabled. Send our ScriptRunner a rerun
                # request. If the request is accepted, we're done.
                success = self._scriptrunner.request_rerun(rerun_data)
                if success:
                    return

        # If we are here, then either we have no ScriptRunner, or our
        # current ScriptRunner is shutting down and cannot handle a rerun
        # request - so we'll create and start a new ScriptRunner.
        self._create_scriptrunner(rerun_data)