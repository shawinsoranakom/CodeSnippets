def test_no_sts_preload_no_middleware(self):
        """
        Don't warn if SecurityMiddleware isn't installed.
        """
        self.assertEqual(base.check_sts_preload(None), [])