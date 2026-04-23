def setUp(self):
        super().setUp()
        self._old_views_urlpatterns = urls.urlpatterns[:]
        urls.urlpatterns += static("media/", document_root=media_dir)