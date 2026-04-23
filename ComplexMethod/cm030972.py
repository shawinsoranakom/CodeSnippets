def wrapper(self, /, *args, **kwargs):
            dry_run = '' in locales
            try:
                import locale
                category = getattr(locale, catstr)
                orig_locale = locale.setlocale(category)
            except AttributeError:
                # if the test author gives us an invalid category string
                raise
            except Exception:
                # cannot retrieve original locale, so do nothing
                pass
            else:
                try:
                    for loc in locales:
                        with self.subTest(locale=loc):
                            try:
                                locale.setlocale(category, loc)
                            except locale.Error:
                                self.skipTest(f'no locale {loc!r}')
                            else:
                                dry_run = False
                                func(self, *args, **kwargs)
                finally:
                    locale.setlocale(category, orig_locale)
            if dry_run:
                # no locales available, so just run the test
                # with the current locale
                with self.subTest(locale=None):
                    func(self, *args, **kwargs)