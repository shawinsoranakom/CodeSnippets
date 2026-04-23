async def test_request_lifecycle_signals_dispatched_with_thread_sensitive(self):
        # Track request_started and request_finished signals.
        signal_handler = SignalHandler()
        request_started.connect(signal_handler)
        self.addCleanup(request_started.disconnect, signal_handler)
        request_finished.connect(signal_handler)
        self.addCleanup(request_finished.disconnect, signal_handler)

        # Perform a basic request.
        application = get_asgi_application()
        scope = self.async_request_factory._base_scope(path="/")
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request"})
        response_start = await communicator.receive_output()
        self.assertEqual(response_start["type"], "http.response.start")
        self.assertEqual(response_start["status"], 200)
        response_body = await communicator.receive_output()
        self.assertEqual(response_body["type"], "http.response.body")
        self.assertEqual(response_body["body"], b"Hello World!")
        # Give response.close() time to finish.
        await communicator.wait()

        # AsyncToSync should have executed the signals in the same thread.
        self.assertEqual(len(signal_handler.calls), 2)
        request_started_call, request_finished_call = signal_handler.calls
        self.assertEqual(
            request_started_call["thread"], request_finished_call["thread"]
        )