def test_response_from_process_exception_when_return_response(self):
        response = self.client.get("/middleware_exceptions/error/")
        self.assertEqual(mw.log, ["process-exception"])
        self.assertEqual(response.content, b"Exception caught")