def test_sanitize_separators(self):
        """
        Tests django.utils.formats.sanitize_separators.
        """
        # Non-strings are untouched
        self.assertEqual(sanitize_separators(123), 123)

        with translation.override("ru", deactivate=True):
            # Russian locale has non-breaking space (\xa0) as thousand
            # separator Usual space is accepted too when sanitizing inputs
            with self.settings(USE_THOUSAND_SEPARATOR=True):
                self.assertEqual(sanitize_separators("1\xa0234\xa0567"), "1234567")
                self.assertEqual(sanitize_separators("77\xa0777,777"), "77777.777")
                self.assertEqual(sanitize_separators("12 345"), "12345")
                self.assertEqual(sanitize_separators("77 777,777"), "77777.777")
            with translation.override(None):
                with self.settings(USE_THOUSAND_SEPARATOR=True, THOUSAND_SEPARATOR="."):
                    self.assertEqual(sanitize_separators("12\xa0345"), "12\xa0345")

        with self.settings(USE_THOUSAND_SEPARATOR=True):
            with patch_formats(
                get_language(), THOUSAND_SEPARATOR=".", DECIMAL_SEPARATOR=","
            ):
                self.assertEqual(sanitize_separators("10.234"), "10234")
                # Suspicion that user entered dot as decimal separator (#22171)
                self.assertEqual(sanitize_separators("10.10"), "10.10")

        with translation.override(None):
            with self.settings(DECIMAL_SEPARATOR=","):
                self.assertEqual(sanitize_separators("1001,10"), "1001.10")
                self.assertEqual(sanitize_separators("1001.10"), "1001.10")
            with self.settings(
                DECIMAL_SEPARATOR=",",
                THOUSAND_SEPARATOR=".",
                USE_THOUSAND_SEPARATOR=True,
            ):
                self.assertEqual(sanitize_separators("1.001,10"), "1001.10")
                self.assertEqual(sanitize_separators("1001,10"), "1001.10")
                self.assertEqual(sanitize_separators("1001.10"), "1001.10")
                # Invalid output.
                self.assertEqual(sanitize_separators("1,001.10"), "1.001.10")