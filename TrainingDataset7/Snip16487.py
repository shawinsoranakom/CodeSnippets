def test_inheritance_2(self):
        Vodcast.objects.create(name="This Week in Django", released=True)
        response = self.client.get(reverse("admin:admin_views_vodcast_changelist"))
        self.assertEqual(response.status_code, 200)