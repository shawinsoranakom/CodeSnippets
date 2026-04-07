def test_implicitly_generated_pk(self):
        post_data = {"name": "1"}
        response = self.client.post(
            reverse("admin:admin_views_implicitlygeneratedpk_add"), post_data
        )
        self.assertEqual(response.status_code, 302)

        post_data = {"name": "2"}
        response = self.client.post(
            reverse("admin:admin_views_implicitlygeneratedpk_change", args=(1,)),
            post_data,
        )
        self.assertEqual(response.status_code, 302)