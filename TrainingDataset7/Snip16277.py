def test_add_query_string_persists(self):
        save_options = [
            {"_addanother": "1"},  # "Save and add another".
            {"_continue": "1"},  # "Save and continue editing".
            {"_saveasnew": "1"},  # "Save as new".
        ]
        other_options = [
            "",
            "_changelist_filters=is_staff__exact%3D0",
            f"{IS_POPUP_VAR}=1",
            f"{TO_FIELD_VAR}=id",
        ]
        url = reverse("admin:auth_user_add")
        for i, save_option in enumerate(save_options):
            for j, other_option in enumerate(other_options):
                with self.subTest(save_option=save_option, other_option=other_option):
                    qsl = "username=newuser"
                    if other_option:
                        qsl = f"{qsl}&{other_option}"
                    response = self.client.post(
                        f"{url}?{qsl}",
                        {
                            "username": f"newuser{i}{j}",
                            "password1": "newpassword",
                            "password2": "newpassword",
                            **save_option,
                        },
                    )
                    parsed_url = urlsplit(response.url)
                    self.assertEqual(parsed_url.query, qsl)