def test_logout_and_password_change_URLs(self):
        response = self.client.get(reverse("admin:admin_views_article_changelist"))
        self.assertContains(
            response,
            '<form id="logout-form" method="post" action="%s">'
            % reverse("admin:logout"),
        )
        self.assertContains(
            response, '<a href="%s">' % reverse("admin:password_change")
        )