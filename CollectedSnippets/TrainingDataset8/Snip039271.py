async def test_events_handled_on_event_loop(self):
        """ScriptRunner events should be handled on the main thread only."""
        session = _create_test_session(asyncio.get_running_loop())

        handle_event_spy = MagicMock(
            side_effect=session._handle_scriptrunner_event_on_event_loop
        )
        session._handle_scriptrunner_event_on_event_loop = handle_event_spy

        # Send a ScriptRunner event from another thread
        thread = threading.Thread(
            target=lambda: session._on_scriptrunner_event(
                sender=MagicMock(), event=ScriptRunnerEvent.SCRIPT_STARTED
            )
        )
        thread.start()
        thread.join()

        # _handle_scriptrunner_event_on_event_loop won't have been called
        # yet, because we haven't yielded the eventloop.
        handle_event_spy.assert_not_called()

        # Yield to let the AppSession's callbacks run.
        # _handle_scriptrunner_event_on_event_loop will be called here.
        await asyncio.sleep(0)

        handle_event_spy.assert_called_once()