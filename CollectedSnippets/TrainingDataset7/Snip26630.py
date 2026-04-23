def test_if_none_match_and_client_error(self):
        def get_response(req):
            resp = self.client.get(req.path_info)
            resp["ETag"] = "spam"
            resp.status_code = 400
            return resp

        self.req.META["HTTP_IF_NONE_MATCH"] = "spam"
        resp = ConditionalGetMiddleware(get_response)(self.req)
        self.assertEqual(resp.status_code, 400)