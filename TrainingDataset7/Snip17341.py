async def test_untouched_request_body_gets_closed(self):
        application = get_asgi_application()
        scope = self.async_request_factory._base_scope(method="POST", path="/post/")
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({"type": "http.request"})
        response_start = await communicator.receive_output()
        self.assertEqual(response_start["type"], "http.response.start")
        self.assertEqual(response_start["status"], 204)
        response_body = await communicator.receive_output()
        self.assertEqual(response_body["type"], "http.response.body")
        self.assertEqual(response_body["body"], b"")
        # Allow response.close() to finish
        await communicator.wait()