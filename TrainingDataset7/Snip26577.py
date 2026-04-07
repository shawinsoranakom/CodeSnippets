def test_append_slash_slashless_unknown(self):
        """
        APPEND_SLASH should not redirect to unknown resources.
        """
        request = self.rf.get("/unknown")
        response = CommonMiddleware(get_response_404)(request)
        self.assertEqual(response.status_code, 404)