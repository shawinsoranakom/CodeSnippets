def __init__(self, script_name: str):
        """Initializes the ScriptRunner for the given script_name"""
        # DeltaGenerator deltas will be enqueued into self.forward_msg_queue.
        self.forward_msg_queue = ForwardMsgQueue()

        main_script_path = os.path.join(
            os.path.dirname(__file__), "test_data", script_name
        )

        super().__init__(
            session_id="test session id",
            main_script_path=main_script_path,
            client_state=ClientState(),
            session_state=SessionState(),
            uploaded_file_mgr=UploadedFileManager(),
            initial_rerun_data=RerunData(),
            user_info={"email": "test@test.com"},
        )

        # Accumulates uncaught exceptions thrown by our run thread.
        self.script_thread_exceptions: List[BaseException] = []

        # Accumulates all ScriptRunnerEvents emitted by us.
        self.events: List[ScriptRunnerEvent] = []
        self.event_data: List[Any] = []

        def record_event(
            sender: Optional[ScriptRunner], event: ScriptRunnerEvent, **kwargs
        ) -> None:
            # Assert that we're not getting unexpected `sender` params
            # from ScriptRunner.on_event
            assert (
                sender is None or sender == self
            ), "Unexpected ScriptRunnerEvent sender!"

            self.events.append(event)
            self.event_data.append(kwargs)

            # Send ENQUEUE_FORWARD_MSGs to our queue
            if event == ScriptRunnerEvent.ENQUEUE_FORWARD_MSG:
                forward_msg = kwargs["forward_msg"]
                self.forward_msg_queue.enqueue(forward_msg)

        self.on_event.connect(record_event, weak=False)