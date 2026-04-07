def test_weak_etag_not_modified(self):
        """
        GZipMiddleware doesn't modify a weak ETag.
        """

        def get_response(req):
            response = HttpResponse(self.compressible_string)
            response.headers["ETag"] = 'W/"eggs"'
            return response

        request = self.rf.get("/", headers={"accept-encoding": "gzip, deflate"})
        gzip_response = GZipMiddleware(get_response)(request)
        self.assertEqual(gzip_response.headers["ETag"], 'W/"eggs"')