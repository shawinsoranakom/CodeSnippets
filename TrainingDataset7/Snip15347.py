def test_callable_urlconf(self):
        """
        Index view should correctly resolve view patterns when ROOT_URLCONF is
        not a string.
        """

        def urlpatterns():
            return (
                path("admin/doc/", include("django.contrib.admindocs.urls")),
                path("admin/", admin.site.urls),
            )

        with self.settings(ROOT_URLCONF=SimpleLazyObject(urlpatterns)):
            response = self.client.get(reverse("django-admindocs-views-index"))
            self.assertEqual(response.status_code, 200)