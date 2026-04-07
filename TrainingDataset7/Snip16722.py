def test_change_view_form_and_formsets_run_validation(self):
        """
        Issue #20522
        Verifying that if the parent form fails validation, the inlines also
        run validation even if validation is contingent on parent form data
        """
        pwdc = ParentWithDependentChildren.objects.create(
            some_required_info=6, family_name="Test1"
        )
        # The form validation should fail because 'some_required_info' is
        # not included on the parent form, and the family_name of the parent
        # does not match that of the child
        post_data = {
            "family_name": "Test2",
            "dependentchild_set-TOTAL_FORMS": "1",
            "dependentchild_set-INITIAL_FORMS": "0",
            "dependentchild_set-MAX_NUM_FORMS": "1",
            "dependentchild_set-0-id": "",
            "dependentchild_set-0-parent": str(pwdc.id),
            "dependentchild_set-0-family_name": "Test1",
        }
        response = self.client.post(
            reverse(
                "admin:admin_views_parentwithdependentchildren_change", args=(pwdc.id,)
            ),
            post_data,
        )
        self.assertFormError(
            response.context["adminform"],
            "some_required_info",
            ["This field is required."],
        )
        self.assertFormSetError(
            response.context["inline_admin_formset"],
            0,
            None,
            [
                "Children must share a family name with their parents in this "
                "contrived test case"
            ],
        )