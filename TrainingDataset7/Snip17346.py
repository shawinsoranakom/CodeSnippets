async def test_assert_in_listen_for_disconnect(self):
        application = get_asgi_application()
        scope = self.async_request_factory._base_scope(path="/")
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request"})
        await communicator.send_input({"type": "http.not_a_real_message"})
        msg = "Invalid ASGI message after request body: http.not_a_real_message"
        with self.assertRaisesMessage(AssertionError, msg):
            await communicator.wait()