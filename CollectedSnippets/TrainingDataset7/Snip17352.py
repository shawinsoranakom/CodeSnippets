async def test_asyncio_cancel_error(self):
        view_started = asyncio.Event()
        # Flag to check if the view was cancelled.
        view_did_cancel = False
        # Track request_finished signal.
        signal_handler = SignalHandler()
        request_finished.connect(signal_handler)
        self.addCleanup(request_finished.disconnect, signal_handler)

        # A view that will listen for the cancelled error.
        async def view(request):
            nonlocal view_did_cancel
            view_started.set()
            try:
                await asyncio.sleep(0.1)
                return HttpResponse("Hello World!")
            except asyncio.CancelledError:
                # Set the flag.
                view_did_cancel = True
                raise

        # Request class to use the view.
        class TestASGIRequest(ASGIRequest):
            urlconf = (path("cancel/", view),)

        # Handler to use request class.
        class TestASGIHandler(ASGIHandler):
            request_class = TestASGIRequest

        # Request cycle should complete since no disconnect was sent.
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
        # Give response.close() time to finish.
        await communicator.wait()
        self.assertIs(view_did_cancel, False)
        # Exactly one call to request_finished handler.
        self.assertEqual(len(signal_handler.calls), 1)
        handler_call = signal_handler.calls.pop()
        # It was NOT on the async thread.
        self.assertNotEqual(handler_call["thread"], threading.current_thread())
        # The signal sender is the handler class.
        self.assertEqual(handler_call["kwargs"], {"sender": TestASGIHandler})
        view_started.clear()

        # Request cycle with a disconnect before the view can respond.
        application = TestASGIHandler()
        scope = self.async_request_factory._base_scope(path="/cancel/")
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request"})
        # Let the view actually start.
        await view_started.wait()
        # Disconnect the client.
        await communicator.send_input({"type": "http.disconnect"})
        # The handler should not send a response.
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