def test_user_permission_performance(self):
        u = User.objects.all()[0]

        # Don't depend on a warm cache, see #17377.
        ContentType.objects.clear_cache()

        with self.assertNumQueries(8):
            response = self.client.get(reverse("admin:auth_user_change", args=(u.pk,)))
            self.assertEqual(response.status_code, 200)