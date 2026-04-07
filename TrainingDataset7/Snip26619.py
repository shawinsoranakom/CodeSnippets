def test_middleware_calculates_etag(self):
        resp = ConditionalGetMiddleware(self.get_response)(self.req)
        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual("", resp["ETag"])