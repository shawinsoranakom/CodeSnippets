def test_set_page_config_reset(self):
        """st.set_page_config should be allowed after a rerun"""

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
        ctx.reset()
        try:
            ctx.on_script_start()
            ctx.enqueue(msg)
        except StreamlitAPIException:
            self.fail("set_page_config should have succeeded after reset!")