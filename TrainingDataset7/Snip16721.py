def test_add_view_form_and_formsets_run_validation(self):
        """
        Issue #20522
        Verifying that if the parent form fails validation, the inlines also
        run validation even if validation is contingent on parent form data.
        Also, assertFormError() and assertFormSetError() is usable for admin
        forms and formsets.
        """
        # The form validation should fail because 'some_required_info' is
        # not included on the parent form, and the family_name of the parent
        # does not match that of the child
        post_data = {
            "family_name": "Test1",
            "dependentchild_set-TOTAL_FORMS": "1",
            "dependentchild_set-INITIAL_FORMS": "0",
            "dependentchild_set-MAX_NUM_FORMS": "1",
            "dependentchild_set-0-id": "",
            "dependentchild_set-0-parent": "",
            "dependentchild_set-0-family_name": "Test2",
        }
        response = self.client.post(
            reverse("admin:admin_views_parentwithdependentchildren_add"), post_data
        )
        self.assertFormError(
            response.context["adminform"],
            "some_required_info",
            ["This field is required."],
        )
        self.assertFormError(response.context["adminform"], None, [])
        self.assertFormSetError(
            response.context["inline_admin_formset"],
            0,
            None,
            [
                "Children must share a family name with their parents in this "
                "contrived test case"
            ],
        )
        self.assertFormSetError(
            response.context["inline_admin_formset"], None, None, []
        )