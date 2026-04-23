def test_no_content_type_nosniff_no_middleware(self):
        """
        Don't warn if SECURE_CONTENT_TYPE_NOSNIFF isn't True and
        SecurityMiddleware isn't in MIDDLEWARE.
        """
        self.assertEqual(base.check_content_type_nosniff(None), [])