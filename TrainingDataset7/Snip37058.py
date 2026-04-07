def tearDown(self):
        super().tearDown()
        urls.urlpatterns = self._old_views_urlpatterns