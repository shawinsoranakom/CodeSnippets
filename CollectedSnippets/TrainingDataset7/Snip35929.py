def test_language_preserved(self):
        with translation.override("fr"):
            management.call_command("dance", verbosity=0)
            self.assertEqual(translation.get_language(), "fr")