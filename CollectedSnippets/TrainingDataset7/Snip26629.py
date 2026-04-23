def test_if_none_match_and_redirect(self):
        def get_response(req):
            resp = self.client.get(req.path_info)
            resp["ETag"] = "spam"
            resp["Location"] = "/"
            resp.status_code = 301
            return resp

        self.req.META["HTTP_IF_NONE_MATCH"] = "spam"
        resp = ConditionalGetMiddleware(get_response)(self.req)
        self.assertEqual(resp.status_code, 301)