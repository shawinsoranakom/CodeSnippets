def setUp(self):
        self._language = get_language()
        self._translations = trans_real._translations
        activate("fr")