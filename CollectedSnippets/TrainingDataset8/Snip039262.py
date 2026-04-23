def test_resets_debug_last_backmsg_id_on_script_finished(self):
        session = _create_test_session()
        session._create_scriptrunner(initial_rerun_data=RerunData())
        session._debug_last_backmsg_id = "some_backmsg_id"

        with patch(
            "streamlit.runtime.app_session.asyncio.get_running_loop",
            return_value=session._event_loop,
        ):
            session._handle_scriptrunner_event_on_event_loop(
                sender=session._scriptrunner,
                event=ScriptRunnerEvent.SCRIPT_STOPPED_WITH_SUCCESS,
                forward_msg=ForwardMsg(),
            )

            self.assertIsNone(session._debug_last_backmsg_id)