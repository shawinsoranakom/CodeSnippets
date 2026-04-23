async def test_streaming(self):
        scope = self.async_request_factory._base_scope(
            path="/streaming/", query_string=b"sleep=0.001"
        )
        application = get_asgi_application()
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request"})
        # Fetch http.response.start.
        await communicator.receive_output(timeout=1)
        # Fetch the 'first' and 'last'.
        first_response = await communicator.receive_output(timeout=1)
        self.assertEqual(first_response["body"], b"first\n")
        second_response = await communicator.receive_output(timeout=1)
        self.assertEqual(second_response["body"], b"last\n")
        # Fetch the rest of the response so that coroutines are cleaned up.
        await communicator.receive_output(timeout=1)
        with self.assertRaises(asyncio.TimeoutError):
            await communicator.receive_output(timeout=1)