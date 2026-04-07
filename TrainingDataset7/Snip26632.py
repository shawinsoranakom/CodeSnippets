def test_no_if_modified_since_and_last_modified(self):
        self.resp_headers["Last-Modified"] = "Sat, 12 Feb 2011 17:38:44 GMT"
        resp = ConditionalGetMiddleware(self.get_response)(self.req)
        self.assertEqual(resp.status_code, 200)