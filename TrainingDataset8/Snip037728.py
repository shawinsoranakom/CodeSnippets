def _handle_rerun_script_request(
        self, client_state: Optional[ClientState] = None
    ) -> None:
        """Tell the ScriptRunner to re-run its script.

        Parameters
        ----------
        client_state : streamlit.proto.ClientState_pb2.ClientState | None
            The ClientState protobuf to run the script with, or None
            to use previous client state.

        """
        self.request_rerun(client_state)