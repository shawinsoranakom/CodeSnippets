async def test_get_asgi_application(self):
        """
        get_asgi_application() returns a functioning ASGI callable.
        """
        application = get_asgi_application()
        # Construct HTTP request.
        scope = self.async_request_factory._base_scope(path="/")
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request"})
        # Read the response.
        response_start = await communicator.receive_output()
        self.assertEqual(response_start["type"], "http.response.start")
        self.assertEqual(response_start["status"], 200)
        self.assertEqual(
            set(response_start["headers"]),
            {
                (b"Content-Length", b"12"),
                (b"Content-Type", b"text/html; charset=utf-8"),
            },
        )
        response_body = await communicator.receive_output()
        self.assertEqual(response_body["type"], "http.response.body")
        self.assertEqual(response_body["body"], b"Hello World!")
        # Allow response.close() to finish.
        await communicator.wait()