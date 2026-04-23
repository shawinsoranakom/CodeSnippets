def test_if_modified_since_and_redirect(self):
        def get_response(req):
            resp = self.client.get(req.path_info)
            resp["Last-Modified"] = "Sat, 12 Feb 2011 17:35:44 GMT"
            resp["Location"] = "/"
            resp.status_code = 301
            return resp

        self.req.META["HTTP_IF_MODIFIED_SINCE"] = "Sat, 12 Feb 2011 17:38:44 GMT"
        resp = ConditionalGetMiddleware(get_response)(self.req)
        self.assertEqual(resp.status_code, 301)