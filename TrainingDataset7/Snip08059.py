def _languages(self):
        if self.languages is not None:
            return self.languages
        return [lang_code for lang_code, _ in settings.LANGUAGES]