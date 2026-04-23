def test_no_etag_no_store_cache(self):
        self.resp_headers["Cache-Control"] = "No-Cache, No-Store, Max-age=0"
        self.assertFalse(
            ConditionalGetMiddleware(self.get_response)(self.req).has_header("ETag")
        )