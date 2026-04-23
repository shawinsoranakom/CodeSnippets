def test_post_messages(self):
        # Ticket 12707: Saving inline editable should not show admin
        # action warnings
        data = {
            "form-TOTAL_FORMS": "3",
            "form-INITIAL_FORMS": "3",
            "form-MAX_NUM_FORMS": "0",
            "form-0-gender": "1",
            "form-0-id": str(self.per1.pk),
            "form-1-gender": "2",
            "form-1-id": str(self.per2.pk),
            "form-2-alive": "checked",
            "form-2-gender": "1",
            "form-2-id": str(self.per3.pk),
            "_save": "Save",
        }
        response = self.client.post(
            reverse("admin:admin_views_person_changelist"), data, follow=True
        )
        self.assertEqual(len(response.context["messages"]), 1)