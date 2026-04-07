def test_response_from_process_exception_short_circuits_remainder(self):
        response = self.client.get("/middleware_exceptions/error/")
        self.assertEqual(mw.log, [])
        self.assertEqual(response.content, b"Exception caught")