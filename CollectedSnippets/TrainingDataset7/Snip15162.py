def test_clear_all_filters_link_callable_filter(self):
        self.client.force_login(self.superuser)
        url = reverse("admin:admin_changelist_band_changelist")
        response = self.client.get(url)
        self.assertNotContains(response, "&#10006; Clear all filters")
        link = '<a href="%s">&#10006; Clear all filters</a>'
        for data, href in (
            ({"nr_of_members_partition": "5"}, "?"),
            (
                {"nr_of_members_partition": "more", "name__startswith": "test"},
                "?name__startswith=test",
            ),
            (
                {"nr_of_members_partition": "5", IS_POPUP_VAR: "id"},
                "?%s=id" % IS_POPUP_VAR,
            ),
        ):
            with self.subTest(data=data):
                response = self.client.get(url, data=data)
                self.assertContains(response, link % href)