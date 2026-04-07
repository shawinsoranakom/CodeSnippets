def test_error_in_titles(self):
        for url, subtitle in [
            (
                reverse("admin:admin_views_article_change", args=(self.a1.pk,)),
                "Article 1 | Change article",
            ),
            (reverse("admin:admin_views_article_add"), "Add article"),
            (reverse("admin:login"), "Log in"),
            (reverse("admin:password_change"), "Password change"),
            (
                reverse("admin:auth_user_password_change", args=(self.superuser.id,)),
                "Change password: super",
            ),
        ]:
            with self.subTest(url=url, subtitle=subtitle):
                response = self.client.post(url, {})
                self.assertContains(response, f"<title>Error: {subtitle}")