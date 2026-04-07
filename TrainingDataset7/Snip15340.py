def test_view_detail_illegal_import(self):
        url = reverse(
            "django-admindocs-views-detail",
            args=["urlpatterns_reverse.nonimported_module.view"],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("urlpatterns_reverse.nonimported_module", sys.modules)