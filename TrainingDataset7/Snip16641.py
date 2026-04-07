def test_group_permission_performance(self):
        g = Group.objects.create(name="test_group")

        # Ensure no queries are skipped due to cached content type for Group.
        ContentType.objects.clear_cache()

        with self.assertNumQueries(6):
            response = self.client.get(reverse("admin:auth_group_change", args=(g.pk,)))
            self.assertEqual(response.status_code, 200)