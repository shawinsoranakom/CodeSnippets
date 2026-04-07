async def test_post_body(self):
        application = get_asgi_application()
        scope = self.async_request_factory._base_scope(
            method="POST",
            path="/post/",
            query_string="echo=1",
        )
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request", "body": b"Echo!"})
        response_start = await communicator.receive_output()
        self.assertEqual(response_start["type"], "http.response.start")
        self.assertEqual(response_start["status"], 200)
        response_body = await communicator.receive_output()
        self.assertEqual(response_body["type"], "http.response.body")
        self.assertEqual(response_body["body"], b"Echo!")