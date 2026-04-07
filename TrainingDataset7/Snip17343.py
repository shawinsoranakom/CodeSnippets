async def test_disconnect(self):
        application = get_asgi_application()
        scope = self.async_request_factory._base_scope(path="/")
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.disconnect"})
        with self.assertRaises(asyncio.TimeoutError):
            await communicator.receive_output()