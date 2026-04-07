def test_single_model_no_append_slash(self):
        self.client.force_login(self.staff_user)
        known_url = reverse("admin9:admin_views_actor_changelist")
        response = self.client.get(known_url[:-1])
        self.assertEqual(response.status_code, 404)