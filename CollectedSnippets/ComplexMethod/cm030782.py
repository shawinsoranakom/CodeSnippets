def test_alt_digits_nl_langinfo(self):
        # Test nl_langinfo(ALT_DIGITS)
        tested = False
        for loc in candidate_locales:
            with self.subTest(locale=loc):
                try:
                    setlocale(LC_TIME, loc)
                except Error:
                    self.skipTest(f'no locale {loc!r}')
                    continue

                with self.subTest(locale=loc):
                    alt_digits = nl_langinfo(locale.ALT_DIGITS)
                    self.assertIsInstance(alt_digits, str)
                    alt_digits = alt_digits.split(';') if alt_digits else []
                    if alt_digits:
                        self.assertGreaterEqual(len(alt_digits), 10, alt_digits)
                    loc1 = loc.split('.', 1)[0]
                    if loc1 in known_alt_digits:
                        count, samples = known_alt_digits[loc1]
                        if count and not alt_digits:
                            self.skipTest(f'ALT_DIGITS is not set for locale {loc!r} on this platform')
                        self.assertEqual(len(alt_digits), count, alt_digits)
                        for i in samples:
                            self.assertEqual(alt_digits[i], samples[i])
                    tested = True
        if not tested:
            self.skipTest('no suitable locales')