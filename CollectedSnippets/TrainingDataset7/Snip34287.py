def test_single_engine_configured(self):
        self.assertEqual(Engine.get_default().file_charset, "abc")