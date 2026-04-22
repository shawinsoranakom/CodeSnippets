def test_disallow_set_page_config_twice(self):
        """st.set_page_config cannot be called twice"""

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

        ctx.on_script_start()

        msg = ForwardMsg()
        msg.page_config_changed.title = "foo"
        ctx.enqueue(msg)

        with self.assertRaises(StreamlitAPIException):
            same_msg = ForwardMsg()
            same_msg.page_config_changed.title = "bar"
            ctx.enqueue(same_msg)