async def test_asyncio_streaming_cancel_error(self):
        # Similar to test_asyncio_cancel_error(), but during a streaming
        # response.
        view_did_cancel = False
        # Track request_finished signals.
        signal_handler = SignalHandler()
        request_finished.connect(signal_handler)
        self.addCleanup(request_finished.disconnect, signal_handler)

        async def streaming_response():
            nonlocal view_did_cancel
            try:
                await asyncio.sleep(0.2)
                yield b"Hello World!"
            except asyncio.CancelledError:
                # Set the flag.
                view_did_cancel = True
                raise

        async def view(request):
            return StreamingHttpResponse(streaming_response())

        class TestASGIRequest(ASGIRequest):
            urlconf = (path("cancel/", view),)

        class TestASGIHandler(ASGIHandler):
            request_class = TestASGIRequest

        # With no disconnect, the request cycle should complete in the same
        # manner as the non-streaming response.
        application = TestASGIHandler()
        scope = self.async_request_factory._base_scope(path="/cancel/")
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request"})
        response_start = await communicator.receive_output()
        self.assertEqual(response_start["type"], "http.response.start")
        self.assertEqual(response_start["status"], 200)
        response_body = await communicator.receive_output()
        self.assertEqual(response_body["type"], "http.response.body")
        self.assertEqual(response_body["body"], b"Hello World!")
        await communicator.wait()
        self.assertIs(view_did_cancel, False)
        # Exactly one call to request_finished handler.
        self.assertEqual(len(signal_handler.calls), 1)
        handler_call = signal_handler.calls.pop()
        # It was NOT on the async thread.
        self.assertNotEqual(handler_call["thread"], threading.current_thread())
        # The signal sender is the handler class.
        self.assertEqual(handler_call["kwargs"], {"sender": TestASGIHandler})

        # Request cycle with a disconnect.
        application = TestASGIHandler()
        scope = self.async_request_factory._base_scope(path="/cancel/")
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request"})
        response_start = await communicator.receive_output()
        # Fetch the start of response so streaming can begin
        self.assertEqual(response_start["type"], "http.response.start")
        self.assertEqual(response_start["status"], 200)
        await asyncio.sleep(0.1)
        # Now disconnect the client.
        await communicator.send_input({"type": "http.disconnect"})
        # This time the handler should not send a response.
        with self.assertRaises(asyncio.TimeoutError):
            await communicator.receive_output()
        await communicator.wait()
        self.assertIs(view_did_cancel, True)
        # Exactly one call to request_finished handler.
        self.assertEqual(len(signal_handler.calls), 1)
        handler_call = signal_handler.calls.pop()
        # It was NOT on the async thread.
        self.assertNotEqual(handler_call["thread"], threading.current_thread())
        # The signal sender is the handler class.
        self.assertEqual(handler_call["kwargs"], {"sender": TestASGIHandler})