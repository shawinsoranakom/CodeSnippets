def test_assert_url_equal(self):
        # Test equality.
        change_user_url = reverse(
            "admin:auth_user_change", args=(self.joepublicuser.pk,)
        )
        self.assertURLEqual(
            "http://testserver{}?_changelist_filters="
            "is_staff__exact%3D0%26is_superuser__exact%3D0".format(change_user_url),
            "http://testserver{}?_changelist_filters="
            "is_staff__exact%3D0%26is_superuser__exact%3D0".format(change_user_url),
        )

        # Test inequality.
        with self.assertRaises(AssertionError):
            self.assertURLEqual(
                "http://testserver{}?_changelist_filters="
                "is_staff__exact%3D0%26is_superuser__exact%3D0".format(change_user_url),
                "http://testserver{}?_changelist_filters="
                "is_staff__exact%3D1%26is_superuser__exact%3D1".format(change_user_url),
            )

        # Ignore scheme and host.
        self.assertURLEqual(
            "http://testserver{}?_changelist_filters="
            "is_staff__exact%3D0%26is_superuser__exact%3D0".format(change_user_url),
            "{}?_changelist_filters="
            "is_staff__exact%3D0%26is_superuser__exact%3D0".format(change_user_url),
        )

        # Ignore ordering of querystring.
        self.assertURLEqual(
            "{}?is_staff__exact=0&is_superuser__exact=0".format(
                reverse("admin:auth_user_changelist")
            ),
            "{}?is_superuser__exact=0&is_staff__exact=0".format(
                reverse("admin:auth_user_changelist")
            ),
        )

        # Ignore ordering of _changelist_filters.
        self.assertURLEqual(
            "{}?_changelist_filters="
            "is_staff__exact%3D0%26is_superuser__exact%3D0".format(change_user_url),
            "{}?_changelist_filters="
            "is_superuser__exact%3D0%26is_staff__exact%3D0".format(change_user_url),
        )