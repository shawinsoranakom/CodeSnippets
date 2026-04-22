def test_set_page_config_first(self):
        """st.set_page_config must be called before other st commands
        when the script has been marked as started"""

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

        markdown_msg = ForwardMsg()
        markdown_msg.delta.new_element.markdown.body = "foo"

        msg = ForwardMsg()
        msg.page_config_changed.title = "foo"

        ctx.enqueue(markdown_msg)
        with self.assertRaises(StreamlitAPIException):
            ctx.enqueue(msg)