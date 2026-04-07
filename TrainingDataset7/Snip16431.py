def test_display_consecutive_whitespace_object_in_breadcrumbs(self):
        user_change_link = reverse("admin:auth_user_change", args=(self.user.pk,))
        cases = [
            (
                self.change_link,
                '<li><a href="/test_admin/admin/admin_views/coverletter/">'
                'Cover letters</a></li><li aria-current="page">-</li>',
            ),
            (
                reverse("admin:admin_views_coverletter_delete", args=(self.obj.pk,)),
                f'<li><a href="{self.change_link}">-</a></li><li aria-current="page">'
                "Delete</li>",
            ),
            (
                reverse("admin:admin_views_coverletter_history", args=(self.obj.pk,)),
                f'<li><a href="{self.change_link}">-</a></li><li aria-current="page">'
                "History</li>",
            ),
            (
                reverse("admin:auth_user_password_change", args=(self.user.pk,)),
                f'<li><a href="{user_change_link}">-</a></li><li aria-current="page">'
                "Change password</li>",
            ),
        ]
        for url, expected_breadcrumbs in cases:
            with self.subTest(url=url, expected_breadcrumbs=expected_breadcrumbs):
                response = self.client.get(url)
                self.assertContains(response, expected_breadcrumbs, html=True)