async def test_wrong_connection_type(self):
        application = get_asgi_application()
        scope = self.async_request_factory._base_scope(path="/", type="other")
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request"})
        msg = "Django can only handle ASGI/HTTP connections, not other."
        with self.assertRaisesMessage(ValueError, msg):
            await communicator.receive_output()