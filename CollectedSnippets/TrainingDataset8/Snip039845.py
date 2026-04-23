def test_stop_script(self):
        """Tests that we can stop a script while it's running."""
        scriptrunner = TestScriptRunner("infinite_loop.py")
        scriptrunner.request_rerun(RerunData())
        scriptrunner.start()

        time.sleep(0.1)
        scriptrunner.request_rerun(RerunData())

        # This test will fail if the script runner does not execute the infinite
        # script's write call at least once during the final script run.
        # The script runs forever, and when we enqueue a rerun it forcibly
        # stops execution and runs some cleanup. If we do not wait for the
        # forced GC to finish, the script won't start running before we stop
        # the script runner, so the expected delta is never created.
        time.sleep(1)
        scriptrunner.request_stop()
        scriptrunner.join()

        self._assert_no_exceptions(scriptrunner)

        # We use _assert_control_events, and not _assert_events,
        # because the infinite loop will fire an indeterminate number of
        # ForwardMsg enqueue requests. Those ForwardMsgs will all be ultimately
        # coalesced down to a single message by the ForwardMsgQueue, which is
        # why the "_assert_text_deltas" call, below, just asserts the existence
        # of a single ForwardMsg.
        self._assert_control_events(
            scriptrunner,
            [
                ScriptRunnerEvent.SCRIPT_STARTED,
                ScriptRunnerEvent.SCRIPT_STOPPED_FOR_RERUN,
                ScriptRunnerEvent.SCRIPT_STARTED,
                ScriptRunnerEvent.SCRIPT_STOPPED_WITH_SUCCESS,
                ScriptRunnerEvent.SHUTDOWN,
            ],
        )
        self._assert_text_deltas(scriptrunner, ["loop_forever"])