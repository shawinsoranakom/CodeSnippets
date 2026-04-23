def test_save_as_new_with_validation_errors(self):
        """
        When you click "Save as new" and have a validation error,
        you only see the "Save as new" button and not the other save buttons,
        and that only the "Save as" button is visible.
        """
        response = self.client.post(
            reverse("admin:admin_views_person_change", args=(self.per1.pk,)),
            {
                "_saveasnew": "",
                "gender": "invalid",
                "_addanother": "fail",
            },
        )
        self.assertContains(response, "Please correct the errors below.")
        self.assertFalse(response.context["show_save_and_add_another"])
        self.assertFalse(response.context["show_save_and_continue"])
        self.assertTrue(response.context["show_save_as_new"])