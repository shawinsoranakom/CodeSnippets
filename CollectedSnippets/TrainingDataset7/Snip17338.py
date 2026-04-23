async def test_request_too_big_request_error(self):
        # Track request_finished signal.
        signal_handler = SignalHandler()
        request_finished.connect(signal_handler)
        self.addCleanup(request_finished.disconnect, signal_handler)

        # Request class that always fails creation with RequestDataTooBig.
        class TestASGIRequest(ASGIRequest):

            def __init__(self, scope, body_file):
                super().__init__(scope, body_file)
                raise RequestDataTooBig()

        # Handler to use the custom request class.
        class TestASGIHandler(ASGIHandler):
            request_class = TestASGIRequest

        application = TestASGIHandler()
        scope = self.async_request_factory._base_scope(path="/not-important/")
        communicator = ApplicationCommunicator(application, scope)

        # Initiate request.
        await communicator.send_input({"type": "http.request"})
        # Give response.close() time to finish.
        await communicator.wait()

        self.assertEqual(len(signal_handler.calls), 1)
        self.assertNotEqual(
            signal_handler.calls[0]["thread"], threading.current_thread()
        )