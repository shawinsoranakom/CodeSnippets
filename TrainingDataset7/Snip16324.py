def test_jsi18n_with_context(self):
        response = self.client.get(reverse("admin-extra-context:jsi18n"))
        self.assertEqual(response.status_code, 200)