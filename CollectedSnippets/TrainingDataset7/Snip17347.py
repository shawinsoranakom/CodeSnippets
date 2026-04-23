async def test_delayed_disconnect_with_body(self):
        application = get_asgi_application()
        scope = self.async_request_factory._base_scope(path="/delayed_hello/")
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request", "body": b"some body"})
        await communicator.send_input({"type": "http.disconnect"})
        with self.assertRaises(asyncio.TimeoutError):
            await communicator.receive_output()