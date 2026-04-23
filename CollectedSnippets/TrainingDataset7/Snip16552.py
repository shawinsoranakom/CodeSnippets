def test_model_delete(self):
        "Check the never-cache status of a model delete page"
        response = self.client.get(
            reverse("admin:admin_views_section_delete", args=(self.s1.pk,))
        )
        self.assertEqual(get_max_age(response), 0)