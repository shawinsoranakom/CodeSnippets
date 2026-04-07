def tearDown(self):
        trans_real._translations = self._old_translations
        activate(self._old_language)