def test_readonly_manytomany(self):
        "Regression test for #13004"
        response = self.client.get(reverse("admin:admin_views_pizza_add"))
        self.assertEqual(response.status_code, 200)