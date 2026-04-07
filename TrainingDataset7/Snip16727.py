def test_missing_get_absolute_url(self):
        "None is returned if model doesn't have get_absolute_url"
        model_admin = ModelAdmin(Worker, None)
        self.assertIsNone(model_admin.get_view_on_site_url(Worker()))