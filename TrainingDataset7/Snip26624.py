def test_etag_extended_cache_control(self):
        self.resp_headers["Cache-Control"] = 'my-directive="my-no-store"'
        self.assertTrue(
            ConditionalGetMiddleware(self.get_response)(self.req).has_header("ETag")
        )