def test_model_view(self):
        "Check the never-cache status of a model edit page"
        response = self.client.get(
            reverse("admin:admin_views_section_change", args=(self.s1.pk,))
        )
        self.assertEqual(get_max_age(response), 0)