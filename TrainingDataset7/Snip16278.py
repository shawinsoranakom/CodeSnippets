def test_change_query_string_persists(self):
        save_options = [
            {"_addanother": "1"},  # "Save and add another".
            {"_continue": "1"},  # "Save and continue editing".
        ]
        other_options = [
            "",
            "_changelist_filters=warm%3D1",
            f"{IS_POPUP_VAR}=1",
            f"{TO_FIELD_VAR}=id",
        ]
        url = reverse("admin:admin_views_color_change", args=(self.color1.pk,))
        for save_option in save_options:
            for other_option in other_options:
                with self.subTest(save_option=save_option, other_option=other_option):
                    qsl = "value=blue"
                    if other_option:
                        qsl = f"{qsl}&{other_option}"
                    response = self.client.post(
                        f"{url}?{qsl}",
                        {
                            "value": "gold",
                            "warm": True,
                            **save_option,
                        },
                    )
                    parsed_url = urlsplit(response.url)
                    self.assertEqual(parsed_url.query, qsl)