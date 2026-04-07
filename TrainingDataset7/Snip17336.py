async def test_headers(self):
        application = get_asgi_application()
        communicator = ApplicationCommunicator(
            application,
            self.async_request_factory._base_scope(
                path="/meta/",
                headers=[
                    [b"content-type", b"text/plain; charset=utf-8"],
                    [b"content-length", b"77"],
                    [b"referer", b"Scotland"],
                    [b"referer", b"Wales"],
                ],
            ),
        )
        await communicator.send_input({"type": "http.request"})
        response_start = await communicator.receive_output()
        self.assertEqual(response_start["type"], "http.response.start")
        self.assertEqual(response_start["status"], 200)
        self.assertEqual(
            set(response_start["headers"]),
            {
                (b"Content-Length", b"19"),
                (b"Content-Type", b"text/plain; charset=utf-8"),
            },
        )
        response_body = await communicator.receive_output()
        self.assertEqual(response_body["type"], "http.response.body")
        self.assertEqual(response_body["body"], b"From Scotland,Wales")
        # Allow response.close() to finish
        await communicator.wait()