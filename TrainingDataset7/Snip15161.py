def test_clear_all_filters_link(self):
        self.client.force_login(self.superuser)
        url = reverse("admin:auth_user_changelist")
        response = self.client.get(url)
        self.assertNotContains(response, "&#10006; Clear all filters")
        link = '<a href="%s">&#10006; Clear all filters</a>'
        for data, href in (
            ({"is_staff__exact": "0"}, "?"),
            (
                {"is_staff__exact": "0", "username__startswith": "test"},
                "?username__startswith=test",
            ),
            (
                {"is_staff__exact": "0", SEARCH_VAR: "test"},
                "?%s=test" % SEARCH_VAR,
            ),
            (
                {"is_staff__exact": "0", IS_POPUP_VAR: "id"},
                "?%s=id" % IS_POPUP_VAR,
            ),
        ):
            with self.subTest(data=data):
                response = self.client.get(url, data=data)
                self.assertContains(response, link % href)