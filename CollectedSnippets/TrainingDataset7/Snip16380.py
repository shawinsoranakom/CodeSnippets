def test_save_as_duplication(self):
        """'save as' creates a new person"""
        post_data = {"_saveasnew": "", "name": "John M", "gender": 1, "age": 42}
        response = self.client.post(
            reverse("admin:admin_views_person_change", args=(self.per1.pk,)), post_data
        )
        self.assertEqual(len(Person.objects.filter(name="John M")), 1)
        self.assertEqual(len(Person.objects.filter(id=self.per1.pk)), 1)
        new_person = Person.objects.latest("id")
        self.assertRedirects(
            response, reverse("admin:admin_views_person_change", args=(new_person.pk,))
        )