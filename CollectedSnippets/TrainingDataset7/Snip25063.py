def test_override_decorator(self):
        @translation.override("pl")
        def func_pl():
            self.assertEqual(get_language(), "pl")

        @translation.override(None)
        def func_none():
            self.assertIsNone(get_language())

        try:
            activate("de")
            func_pl()
            self.assertEqual(get_language(), "de")
            func_none()
            self.assertEqual(get_language(), "de")
        finally:
            deactivate()