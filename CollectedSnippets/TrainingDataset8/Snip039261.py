def test_ignore_events_from_noncurrent_scriptrunner(self, mock_enqueue: MagicMock):
        """If we receive ScriptRunnerEvents from anything other than our
        current ScriptRunner, we should silently ignore them.
        """
        session = _create_test_session()
        session._create_scriptrunner(initial_rerun_data=RerunData())

        # Our test AppSession is created with a mock EventLoop, so
        # we pretend that this function is called on that same mock EventLoop.
        with patch(
            "streamlit.runtime.app_session.asyncio.get_running_loop",
            return_value=session._event_loop,
        ):
            session._handle_scriptrunner_event_on_event_loop(
                sender=session._scriptrunner,
                event=ScriptRunnerEvent.ENQUEUE_FORWARD_MSG,
                forward_msg=ForwardMsg(),
            )
            mock_enqueue.assert_called_once_with(ForwardMsg())

            mock_enqueue.reset_mock()

            non_current_scriptrunner = MagicMock(spec=ScriptRunner)
            session._handle_scriptrunner_event_on_event_loop(
                sender=non_current_scriptrunner,
                event=ScriptRunnerEvent.ENQUEUE_FORWARD_MSG,
                forward_msg=ForwardMsg(),
            )
            mock_enqueue.assert_not_called()