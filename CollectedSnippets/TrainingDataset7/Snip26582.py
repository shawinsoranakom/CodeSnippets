def test_append_slash_disabled(self):
        """
        Disabling append slash functionality should leave slashless URLs alone.
        """
        request = self.rf.get("/slash")
        self.assertEqual(CommonMiddleware(get_response_404)(request).status_code, 404)