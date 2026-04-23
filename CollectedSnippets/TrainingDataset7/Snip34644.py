def test_exc_info(self):
        client = Client(raise_request_exception=False)
        response = client.get("/broken_view/")
        self.assertEqual(response.status_code, 500)
        exc_type, exc_value, exc_traceback = response.exc_info
        self.assertIs(exc_type, KeyError)
        self.assertIsInstance(exc_value, KeyError)
        self.assertEqual(str(exc_value), "'Oops! Looks like you wrote some bad code.'")
        self.assertIsNotNone(exc_traceback)