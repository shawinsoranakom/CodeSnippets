def test_custom_pk(self):
        Language.objects.create(iso="en", name="English", english_name="English")
        response = self.client.get(reverse("admin:admin_views_language_changelist"))
        self.assertEqual(response.status_code, 200)