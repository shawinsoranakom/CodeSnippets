def test_strong_etag_modified(self):
        """
        GZipMiddleware makes a strong ETag weak.
        """

        def get_response(req):
            response = HttpResponse(self.compressible_string)
            response.headers["ETag"] = '"eggs"'
            return response

        request = self.rf.get("/", headers={"accept-encoding": "gzip, deflate"})
        gzip_response = GZipMiddleware(get_response)(request)
        self.assertEqual(gzip_response.headers["ETag"], 'W/"eggs"')