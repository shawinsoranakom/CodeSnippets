def test_with_content_type_nosniff(self):
        self.assertEqual(base.check_content_type_nosniff(None), [])