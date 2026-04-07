def test_if_modified_since_and_last_modified_in_the_future(self):
        self.req.META["HTTP_IF_MODIFIED_SINCE"] = "Sat, 12 Feb 2011 17:38:44 GMT"
        self.resp_headers["Last-Modified"] = "Sat, 12 Feb 2011 17:41:44 GMT"
        self.resp = ConditionalGetMiddleware(self.get_response)(self.req)
        self.assertEqual(self.resp.status_code, 200)