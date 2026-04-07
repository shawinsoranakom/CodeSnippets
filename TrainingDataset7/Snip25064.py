def test_override_exit(self):
        """
        The language restored is the one used when the function was
        called, not the one used when the decorator was initialized (#23381).
        """
        activate("fr")

        @translation.override("pl")
        def func_pl():
            pass

        deactivate()

        try:
            activate("en")
            func_pl()
            self.assertEqual(get_language(), "en")
        finally:
            deactivate()