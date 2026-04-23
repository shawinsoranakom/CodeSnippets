def test_no_len_type(self):
        self.assertEqual(pluralize(object(), "y,es"), "")
        self.assertEqual(pluralize(object(), "es"), "")