def test_view_on_site_url_non_integer_ids(self):
        """The view_on_site URL accepts non-integer ids."""
        self.assertEqual(
            reverse(
                "admin:view_on_site",
                kwargs={
                    "content_type_id": "37156b6a-8a82",
                    "object_id": "37156b6a-8a83",
                },
            ),
            "/test_admin/admin/r/37156b6a-8a82/37156b6a-8a83/",
        )