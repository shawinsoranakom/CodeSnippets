def test_post_save_change_redirect(self):
        """
        ModelAdmin.response_post_save_change() controls the redirection after
        the 'Save' button has been pressed when editing an existing object.
        """
        Person.objects.create(name="John Doe")
        self.assertEqual(Person.objects.count(), 1)
        person = Person.objects.all()[0]
        post_url = reverse(
            "admin_custom_urls:admin_custom_urls_person_change", args=[person.pk]
        )
        response = self.client.post(post_url, {"name": "Jack Doe"})
        self.assertRedirects(
            response,
            reverse(
                "admin_custom_urls:admin_custom_urls_person_delete", args=[person.pk]
            ),
        )