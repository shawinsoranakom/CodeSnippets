def test_if_none_match_and_same_etag(self):
        self.req.META["HTTP_IF_NONE_MATCH"] = '"spam"'
        self.resp_headers["ETag"] = '"spam"'
        resp = ConditionalGetMiddleware(self.get_response)(self.req)
        self.assertEqual(resp.status_code, 304)