def test_no_sts_preload_no_seconds(self):
        """
        Don't warn if SECURE_HSTS_SECONDS isn't set.
        """
        self.assertEqual(base.check_sts_preload(None), [])