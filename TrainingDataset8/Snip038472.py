def setUp(self):
        self.forward_msg_queue = ForwardMsgQueue()
        self.orig_report_ctx = None
        self.new_script_run_ctx = ScriptRunContext(
            session_id="test session id",
            _enqueue=self.forward_msg_queue.enqueue,
            query_string="",
            session_state=SafeSessionState(SessionState()),
            uploaded_file_mgr=UploadedFileManager(),
            page_script_hash="",
            user_info={"email": "test@test.com"},
        )

        self.orig_report_ctx = get_script_run_ctx()
        add_script_run_ctx(threading.current_thread(), self.new_script_run_ctx)

        self.app_session = FakeAppSession()

        # Create a MemoryMediaFileStorage instance, and the MediaFileManager
        # singleton.
        self.media_file_storage = MemoryMediaFileStorage(MEDIA_ENDPOINT)

        mock_runtime = MagicMock(spec=Runtime)
        mock_runtime.media_file_mgr = MediaFileManager(self.media_file_storage)
        Runtime._instance = mock_runtime