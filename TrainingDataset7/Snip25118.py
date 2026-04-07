def test_get_language_from_path_null(self):
        g = trans_null.get_language_from_path
        self.assertIsNone(g("/pl/"))
        self.assertIsNone(g("/pl"))
        self.assertIsNone(g("/xyz/"))