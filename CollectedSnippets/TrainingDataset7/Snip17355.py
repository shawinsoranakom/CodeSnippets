async def test_streaming_disconnect(self):
        scope = self.async_request_factory._base_scope(
            path="/streaming/", query_string=b"sleep=0.1"
        )
        application = get_asgi_application()
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request"})
        await communicator.receive_output(timeout=1)
        first_response = await communicator.receive_output(timeout=1)
        self.assertEqual(first_response["body"], b"first\n")
        # Disconnect the client.
        await communicator.send_input({"type": "http.disconnect"})
        # 'last\n' isn't sent.
        with self.assertRaises(asyncio.TimeoutError):
            await communicator.receive_output(timeout=0.2)