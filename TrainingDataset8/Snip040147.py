def test_st_user_reads_from_context_(self):
        """Test that st.user reads information from current ScriptRunContext
        And after ScriptRunContext changed, it returns new email
        """
        orig_report_ctx = get_script_run_ctx()

        forward_msg_queue = ForwardMsgQueue()

        try:
            add_script_run_ctx(
                threading.current_thread(),
                ScriptRunContext(
                    session_id="test session id",
                    _enqueue=forward_msg_queue.enqueue,
                    query_string="",
                    session_state=SafeSessionState(SessionState()),
                    uploaded_file_mgr=None,
                    page_script_hash="",
                    user_info={"email": "something@else.com"},
                ),
            )

            self.assertEqual(st.experimental_user.email, "something@else.com")
        except Exception as e:
            raise e
        finally:
            add_script_run_ctx(threading.current_thread(), orig_report_ctx)