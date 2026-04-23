def test_append_slash_opt_out(self):
        """
        Views marked with @no_append_slash should be left alone.
        """
        request = self.rf.get("/sensitive_fbv")
        self.assertEqual(CommonMiddleware(get_response_404)(request).status_code, 404)

        request = self.rf.get("/sensitive_cbv")
        self.assertEqual(CommonMiddleware(get_response_404)(request).status_code, 404)