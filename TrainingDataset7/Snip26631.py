def test_if_modified_since_and_no_last_modified(self):
        self.req.META["HTTP_IF_MODIFIED_SINCE"] = "Sat, 12 Feb 2011 17:38:44 GMT"
        resp = ConditionalGetMiddleware(self.get_response)(self.req)
        self.assertEqual(resp.status_code, 200)