def test_if_modified_since_and_client_error(self):
        def get_response(req):
            resp = self.client.get(req.path_info)
            resp["Last-Modified"] = "Sat, 12 Feb 2011 17:35:44 GMT"
            resp.status_code = 400
            return resp

        self.req.META["HTTP_IF_MODIFIED_SINCE"] = "Sat, 12 Feb 2011 17:38:44 GMT"
        resp = ConditionalGetMiddleware(get_response)(self.req)
        self.assertEqual(resp.status_code, 400)