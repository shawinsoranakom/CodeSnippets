def setUp(self):
        self._old_language = get_language()
        self.addCleanup(activate, self._old_language)