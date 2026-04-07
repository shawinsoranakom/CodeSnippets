def test_formset_with_deletion_remove_deletion_flag(self):
        """
        If a form is filled with something and can_delete is also checked, that
        form's errors shouldn't make the entire formset invalid since it's
        going to be deleted.
        """

        class CheckForm(Form):
            field = IntegerField(min_value=100)

        data = {
            "check-TOTAL_FORMS": "3",  # the number of forms rendered
            "check-INITIAL_FORMS": "2",  # the number of forms with initial data
            "choices-MIN_NUM_FORMS": "0",  # min number of forms
            "check-MAX_NUM_FORMS": "0",  # max number of forms
            "check-0-field": "200",
            "check-0-DELETE": "",
            "check-1-field": "50",
            "check-1-DELETE": "on",
            "check-2-field": "",
            "check-2-DELETE": "",
        }
        CheckFormSet = formset_factory(CheckForm, can_delete=True)
        formset = CheckFormSet(data, prefix="check")
        self.assertTrue(formset.is_valid())
        # If the deletion flag is removed, validation is enabled.
        data["check-1-DELETE"] = ""
        formset = CheckFormSet(data, prefix="check")
        self.assertFalse(formset.is_valid())