async def test_asgi_cookies(self):
        application = get_asgi_application()
        scope = self.async_request_factory._base_scope(path="/cookie/")
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request"})
        response_start = await communicator.receive_output()
        self.assertIn((b"Set-Cookie", b"key=value; Path=/"), response_start["headers"])
        # Allow response.close() to finish.
        await communicator.wait()