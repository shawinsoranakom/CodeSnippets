def test_invalid_appindex_url(self):
        """
        #21056 -- URL reversing shouldn't work for nonexistent apps.
        """
        good_url = "/test_admin/admin/admin_views/"
        confirm_good_url = reverse(
            "admin:app_list", kwargs={"app_label": "admin_views"}
        )
        self.assertEqual(good_url, confirm_good_url)

        with self.assertRaises(NoReverseMatch):
            reverse("admin:app_list", kwargs={"app_label": "this_should_fail"})
        with self.assertRaises(NoReverseMatch):
            reverse("admin:app_list", args=("admin_views2",))