def test_save_as_continue_false(self):
        """
        Saving a new object using "Save as new" redirects to the changelist
        instead of the change view when ModelAdmin.save_as_continue=False.
        """
        post_data = {"_saveasnew": "", "name": "John M", "gender": 1, "age": 42}
        url = reverse(
            "admin:admin_views_person_change",
            args=(self.per1.pk,),
            current_app=site2.name,
        )
        response = self.client.post(url, post_data)
        self.assertEqual(len(Person.objects.filter(name="John M")), 1)
        self.assertEqual(len(Person.objects.filter(id=self.per1.pk)), 1)
        self.assertRedirects(
            response,
            reverse("admin:admin_views_person_changelist", current_app=site2.name),
        )