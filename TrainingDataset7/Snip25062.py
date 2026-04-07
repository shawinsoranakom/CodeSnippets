def test_override(self):
        activate("de")
        try:
            with translation.override("pl"):
                self.assertEqual(get_language(), "pl")
            self.assertEqual(get_language(), "de")
            with translation.override(None):
                self.assertIsNone(get_language())
                with translation.override("pl"):
                    pass
                self.assertIsNone(get_language())
            self.assertEqual(get_language(), "de")
        finally:
            deactivate()