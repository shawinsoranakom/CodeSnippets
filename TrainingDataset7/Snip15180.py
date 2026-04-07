def test_search_bar_total_link_preserves_options(self):
        self.client.force_login(self.superuser)
        url = reverse("admin:auth_user_changelist")
        for data, href in (
            ({"is_staff__exact": "0"}, "?"),
            ({"is_staff__exact": "0", IS_POPUP_VAR: "1"}, f"?{IS_POPUP_VAR}=1"),
            ({"is_staff__exact": "0", IS_FACETS_VAR: ""}, f"?{IS_FACETS_VAR}"),
            (
                {"is_staff__exact": "0", IS_POPUP_VAR: "1", IS_FACETS_VAR: ""},
                f"?{IS_POPUP_VAR}=1&{IS_FACETS_VAR}",
            ),
        ):
            with self.subTest(data=data):
                response = self.client.get(url, data=data)
                self.assertContains(
                    response, f'0 results (<a href="{href}">1 total</a>)'
                )