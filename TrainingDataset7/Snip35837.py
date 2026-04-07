def test_reverse_inner_in_response_middleware(self):
        """
        Test reversing an URL from the *overridden* URLconf from inside
        a response middleware.
        """
        response = self.client.get("/second_test/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"/second_test/")