def test_non_form_errors_is_errorlist(self):
        # test if non-form errors are correctly handled; ticket #12878
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": str(self.per2.pk),
            "form-0-alive": "1",
            "form-0-gender": "2",
            "_save": "Save",
        }
        response = self.client.post(
            reverse("admin:admin_views_person_changelist"), data
        )
        non_form_errors = response.context["cl"].formset.non_form_errors()
        self.assertIsInstance(non_form_errors, ErrorList)
        self.assertEqual(
            str(non_form_errors),
            str(ErrorList(["Grace is not a Zombie"], error_class="nonform")),
        )