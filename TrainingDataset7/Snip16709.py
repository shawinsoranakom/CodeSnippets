def test_url_prefix(self):
        context = {
            "preserved_filters": self.get_preserved_filters_querystring(),
            "opts": User._meta,
        }
        prefixes = ("", "/prefix/", "/後台/")
        for prefix in prefixes:
            with self.subTest(prefix=prefix), override_script_prefix(prefix):
                url = reverse(
                    "admin:auth_user_changelist", current_app=self.admin_site.name
                )
                self.assertURLEqual(
                    self.get_changelist_url(),
                    add_preserved_filters(context, url),
                )