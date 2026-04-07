def tearDown(self):
        trans_real._translations = self._translations
        activate(self._old_language)