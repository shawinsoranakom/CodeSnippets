def test_post_save_add_redirect(self):
        """
        ModelAdmin.response_post_save_add() controls the redirection after
        the 'Save' button has been pressed when adding a new object.
        """
        post_data = {"name": "John Doe"}
        self.assertEqual(Person.objects.count(), 0)
        response = self.client.post(
            reverse("admin_custom_urls:admin_custom_urls_person_add"), post_data
        )
        persons = Person.objects.all()
        self.assertEqual(len(persons), 1)
        redirect_url = reverse(
            "admin_custom_urls:admin_custom_urls_person_history", args=[persons[0].pk]
        )
        self.assertRedirects(response, redirect_url)