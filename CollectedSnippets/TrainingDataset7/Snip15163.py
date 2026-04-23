def test_no_clear_all_filters_link(self):
        self.client.force_login(self.superuser)
        url = reverse("admin:auth_user_changelist")
        link = ">&#10006; Clear all filters</a>"
        for data in (
            {SEARCH_VAR: "test"},
            {ORDER_VAR: "-1"},
            {TO_FIELD_VAR: "id"},
            {PAGE_VAR: "1"},
            {IS_POPUP_VAR: "1"},
            {IS_FACETS_VAR: ""},
            {"username__startswith": "test"},
        ):
            with self.subTest(data=data):
                response = self.client.get(url, data=data)
                self.assertNotContains(response, link)