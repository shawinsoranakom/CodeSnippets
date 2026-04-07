def test_aria_describedby_for_add_and_change_links(self):
        response = self.client.get(reverse("admin:index"))
        tests = [
            ("admin_views", "actor"),
            ("admin_views", "worker"),
            ("auth", "group"),
            ("auth", "user"),
        ]
        for app_label, model_name in tests:
            with self.subTest(app_label=app_label, model_name=model_name):
                row_id = f"{app_label}-{model_name}"
                self.assertContains(response, f'<th scope="row" id="{row_id}">')
                self.assertContains(
                    response,
                    f'<a href="/test_admin/admin/{app_label}/{model_name}/" '
                    f'class="changelink" aria-describedby="{row_id}">Change</a>',
                )
                self.assertContains(
                    response,
                    f'<a href="/test_admin/admin/{app_label}/{model_name}/add/" '
                    f'class="addlink" aria-describedby="{row_id}">Add</a>',
                )