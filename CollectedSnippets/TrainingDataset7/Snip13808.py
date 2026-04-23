def rtl(self):
        with self.desktop_size():
            with override_settings(LANGUAGE_CODE=settings.LANGUAGES_BIDI[-1]):
                yield