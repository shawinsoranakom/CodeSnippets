async def test_get_query_string(self):
        application = get_asgi_application()
        for query_string in (b"name=Andrew", "name=Andrew"):
            with self.subTest(query_string=query_string):
                scope = self.async_request_factory._base_scope(
                    path="/",
                    query_string=query_string,
                )
                communicator = ApplicationCommunicator(application, scope)
                await communicator.send_input({"type": "http.request"})
                response_start = await communicator.receive_output()
                self.assertEqual(response_start["type"], "http.response.start")
                self.assertEqual(response_start["status"], 200)
                response_body = await communicator.receive_output()
                self.assertEqual(response_body["type"], "http.response.body")
                self.assertEqual(response_body["body"], b"Hello Andrew!")
                # Allow response.close() to finish
                await communicator.wait()