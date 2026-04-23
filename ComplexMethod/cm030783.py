def test_era_nl_langinfo(self):
        # Test nl_langinfo(ERA)
        tested = False
        for loc in candidate_locales:
            with self.subTest(locale=loc):
                try:
                    setlocale(LC_TIME, loc)
                except Error:
                    self.skipTest(f'no locale {loc!r}')
                    continue

                with self.subTest(locale=loc):
                    era = nl_langinfo(locale.ERA)
                    self.assertIsInstance(era, str)
                    if era:
                        self.assertEqual(era.count(':'), (era.count(';') + 1) * 5, era)

                    loc1 = loc.split('.', 1)[0]
                    if loc1 in known_era:
                        count, sample = known_era[loc1]
                        if count:
                            if not era:
                                self.skipTest(f'ERA is not set for locale {loc!r} on this platform')
                            self.assertGreaterEqual(era.count(';') + 1, count)
                            self.assertIn(sample, era)
                        else:
                            self.assertEqual(era, '')
                    tested = True
        if not tested:
            self.skipTest('no suitable locales')