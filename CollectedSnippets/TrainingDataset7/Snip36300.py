def test_get_default_encoding(self):
        with mock.patch("locale.getlocale", side_effect=Exception):
            self.assertEqual(get_system_encoding(), "ascii")