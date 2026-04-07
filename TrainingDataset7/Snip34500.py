def test_middleware_caching(self):
        response = self.client.get("/template_response_view/")
        self.assertEqual(response.status_code, 200)

        time.sleep(1.0)

        response2 = self.client.get("/template_response_view/")
        self.assertEqual(response2.status_code, 200)

        self.assertEqual(response.content, response2.content)

        time.sleep(2.0)

        # Let the cache expire and test again
        response2 = self.client.get("/template_response_view/")
        self.assertEqual(response2.status_code, 200)

        self.assertNotEqual(response.content, response2.content)