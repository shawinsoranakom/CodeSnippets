def test_multiple_engines_configured(self):
        self.assertEqual(Engine.get_default().file_charset, "abc")