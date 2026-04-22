def __init__(
        self,
        session_id: str,
        main_script_path: str,
        client_state: ClientState,
        session_state: SessionState,
        uploaded_file_mgr: UploadedFileManager,
        initial_rerun_data: RerunData,
        user_info: Dict[str, Optional[str]],
    ):
        """Initialize the ScriptRunner.

        (The ScriptRunner won't start executing until start() is called.)

        Parameters
        ----------
        session_id : str
            The AppSession's id.

        main_script_path : str
            Path to our main app script.

        client_state : ClientState
            The current state from the client (widgets and query params).

        uploaded_file_mgr : UploadedFileManager
            The File manager to store the data uploaded by the file_uploader widget.

        user_info: Dict
            A dict that contains information about the current user. For now,
            it only contains the user's email address.

            {
                "email": "example@example.com"
            }

            Information about the current user is optionally provided when a
            websocket connection is initialized via the "X-Streamlit-User" header.

        """
        self._session_id = session_id
        self._main_script_path = main_script_path
        self._uploaded_file_mgr = uploaded_file_mgr
        self._user_info = user_info

        # Initialize SessionState with the latest widget states
        session_state.set_widgets_from_proto(client_state.widget_states)

        self._client_state = client_state
        self._session_state = SafeSessionState(session_state)

        self._requests = ScriptRequests()
        self._requests.request_rerun(initial_rerun_data)

        self.on_event = Signal(
            doc="""Emitted when a ScriptRunnerEvent occurs.

            This signal is generally emitted on the ScriptRunner's script
            thread (which is *not* the same thread that the ScriptRunner was
            created on).

            Parameters
            ----------
            sender: ScriptRunner
                The sender of the event (this ScriptRunner).

            event : ScriptRunnerEvent

            forward_msg : ForwardMsg | None
                The ForwardMsg to send to the frontend. Set only for the
                ENQUEUE_FORWARD_MSG event.

            exception : BaseException | None
                Our compile error. Set only for the
                SCRIPT_STOPPED_WITH_COMPILE_ERROR event.

            widget_states : streamlit.proto.WidgetStates_pb2.WidgetStates | None
                The ScriptRunner's final WidgetStates. Set only for the
                SHUTDOWN event.
            """
        )

        # Set to true while we're executing. Used by
        # _maybe_handle_execution_control_request.
        self._execing = False

        # This is initialized in start()
        self._script_thread: Optional[threading.Thread] = None