def test_render_views_no_subtitle(self):
        tests = [
            reverse("admin:index"),
            reverse("admin:password_change"),
            reverse("admin:app_list", args=("admin_views",)),
            reverse("admin:admin_views_article_delete", args=(self.a1.pk,)),
            reverse("admin:admin_views_article_history", args=(self.a1.pk,)),
        ]
        for url in tests:
            with self.subTest(url=url):
                with self.assertNoLogs("django.template", "DEBUG"):
                    self.client.get(url)
        # Login must be after logout.
        with self.assertNoLogs("django.template", "DEBUG"):
            self.client.post(reverse("admin:logout"))
            self.client.get(reverse("admin:login"))