def test_dont_enqueue_with_pending_script_request(self):
        """No ForwardMsgs are enqueued when the ScriptRunner has
        a STOP or RERUN request.
        """
        # Create a ScriptRunner and pretend that we've already started
        # executing.
        runner = TestScriptRunner("not_a_script.py")
        runner._is_in_script_thread = MagicMock(return_value=True)
        runner._execing = True
        runner._requests._state = ScriptRequestType.CONTINUE

        # Enqueue a ForwardMsg on the runner, and ensure it's delivered
        # to event listeners. (We're not stopped yet.)
        mock_msg = MagicMock()
        runner._enqueue_forward_msg(mock_msg)
        self._assert_forward_msgs(runner, [mock_msg])

        runner.clear_forward_msgs()

        # Now, "stop" our ScriptRunner. Enqueuing should result in
        # a StopException being raised, and no message enqueued.
        runner._requests.request_stop()
        with self.assertRaises(StopException):
            runner._enqueue_forward_msg(MagicMock())
        self._assert_forward_msgs(runner, [])

        # And finally, request a rerun. Enqueuing should result in
        # a RerunException being raised and no message enqueued.
        runner._requests = ScriptRequests()
        runner.request_rerun(RerunData())
        with self.assertRaises(RerunException):
            runner._enqueue_forward_msg(MagicMock())
        self._assert_forward_msgs(runner, [])