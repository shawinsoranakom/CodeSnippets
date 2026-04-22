def test_set_page_config_immutable(self):
        """st.set_page_config must be called at most once"""

        fake_enqueue = lambda msg: None
        ctx = ScriptRunContext(
            session_id="TestSessionID",
            _enqueue=fake_enqueue,
            query_string="",
            session_state=SafeSessionState(SessionState()),
            uploaded_file_mgr=UploadedFileManager(),
            page_script_hash="",
            user_info={"email": "test@test.com"},
        )

        msg = ForwardMsg()
        msg.page_config_changed.title = "foo"

        ctx.enqueue(msg)
        with self.assertRaises(StreamlitAPIException):
            ctx.enqueue(msg)