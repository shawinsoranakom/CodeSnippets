def test_no_content_type_nosniff(self):
        """
        Warn if SECURE_CONTENT_TYPE_NOSNIFF isn't True.
        """
        self.assertEqual(base.check_content_type_nosniff(None), [base.W006])