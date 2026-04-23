def setUpClass(cls):
        super().setUpClass()
        cls._article_get_latest_by = Article._meta.get_latest_by