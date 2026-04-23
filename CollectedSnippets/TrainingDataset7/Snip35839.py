def test_reverse_inner_in_streaming(self):
        """
        Test reversing an URL from the *overridden* URLconf from inside
        a streaming response.
        """
        response = self.client.get("/second_test/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b"".join(response), b"/second_test/")