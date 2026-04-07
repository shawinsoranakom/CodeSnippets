def test_validate_max_ignores_forms_marked_for_deletion(self):
        class CheckForm(Form):
            field = IntegerField()

        data = {
            "check-TOTAL_FORMS": "2",
            "check-INITIAL_FORMS": "0",
            "check-MAX_NUM_FORMS": "1",
            "check-0-field": "200",
            "check-0-DELETE": "",
            "check-1-field": "50",
            "check-1-DELETE": "on",
        }
        CheckFormSet = formset_factory(
            CheckForm, max_num=1, validate_max=True, can_delete=True
        )
        formset = CheckFormSet(data, prefix="check")
        self.assertTrue(formset.is_valid())