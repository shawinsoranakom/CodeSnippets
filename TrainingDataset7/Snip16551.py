def test_model_history(self):
        "Check the never-cache status of a model history page"
        response = self.client.get(
            reverse("admin:admin_views_section_history", args=(self.s1.pk,))
        )
        self.assertEqual(get_max_age(response), 0)