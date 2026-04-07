def test_non_form_errors(self):
        # test if non-form errors are handled; ticket #12716
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": str(self.per2.pk),
            "form-0-alive": "1",
            "form-0-gender": "2",
            # The form processing understands this as a list_editable "Save"
            # and not an action "Go".
            "_save": "Save",
        }
        response = self.client.post(
            reverse("admin:admin_views_person_changelist"), data
        )
        self.assertContains(response, "Grace is not a Zombie")