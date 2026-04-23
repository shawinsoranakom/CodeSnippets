def test_etag_match(self):
        """
        GZipMiddleware allows 304 Not Modified responses.
        """

        def get_response(req):
            return HttpResponse(self.compressible_string)

        def get_cond_response(req):
            return ConditionalGetMiddleware(get_response)(req)

        request = self.rf.get("/", headers={"accept-encoding": "gzip, deflate"})
        response = GZipMiddleware(get_cond_response)(request)
        gzip_etag = response.headers["ETag"]
        next_request = self.rf.get(
            "/",
            headers={"accept-encoding": "gzip, deflate", "if-none-match": gzip_etag},
        )
        next_response = ConditionalGetMiddleware(get_response)(next_request)
        self.assertEqual(next_response.status_code, 304)