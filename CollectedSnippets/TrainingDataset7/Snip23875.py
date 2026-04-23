def tearDown(self):
        Article._meta.get_latest_by = self._article_get_latest_by