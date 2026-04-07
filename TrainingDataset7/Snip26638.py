def test_not_modified_headers(self):
        """
        The 304 Not Modified response should include only the headers required
        by RFC 9110 Section 15.4.5, Last-Modified, and the cookies.
        """

        def get_response(req):
            resp = self.client.get(req.path_info)
            resp["Date"] = "Sat, 12 Feb 2011 17:35:44 GMT"
            resp["Last-Modified"] = "Sat, 12 Feb 2011 17:35:44 GMT"
            resp["Expires"] = "Sun, 13 Feb 2011 17:35:44 GMT"
            resp["Vary"] = "Cookie"
            resp["Cache-Control"] = "public"
            resp["Content-Location"] = "/alt"
            resp["Content-Language"] = "en"  # shouldn't be preserved
            resp["ETag"] = '"spam"'
            resp.set_cookie("key", "value")
            return resp

        self.req.META["HTTP_IF_NONE_MATCH"] = '"spam"'

        new_response = ConditionalGetMiddleware(get_response)(self.req)
        self.assertEqual(new_response.status_code, 304)
        base_response = get_response(self.req)
        for header in (
            "Cache-Control",
            "Content-Location",
            "Date",
            "ETag",
            "Expires",
            "Last-Modified",
            "Vary",
        ):
            self.assertEqual(
                new_response.headers[header], base_response.headers[header]
            )
        self.assertEqual(new_response.cookies, base_response.cookies)
        self.assertNotIn("Content-Language", new_response)