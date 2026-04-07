def test_middleware_wont_overwrite_etag(self):
        self.resp_headers["ETag"] = "eggs"
        resp = ConditionalGetMiddleware(self.get_response)(self.req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual("eggs", resp["ETag"])