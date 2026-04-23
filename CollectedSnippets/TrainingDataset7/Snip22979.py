def test_formset_validate_max_flag_custom_error(self):
        data = {
            "choices-TOTAL_FORMS": "2",
            "choices-INITIAL_FORMS": "0",
            "choices-MIN_NUM_FORMS": "0",
            "choices-MAX_NUM_FORMS": "2",
            "choices-0-choice": "Zero",
            "choices-0-votes": "0",
            "choices-1-choice": "One",
            "choices-1-votes": "1",
        }
        ChoiceFormSet = formset_factory(Choice, extra=1, max_num=1, validate_max=True)
        formset = ChoiceFormSet(
            data,
            auto_id=False,
            prefix="choices",
            error_messages={
                "too_many_forms": "Number of submitted forms should be at most %(num)d."
            },
        )
        self.assertFalse(formset.is_valid())
        self.assertEqual(
            formset.non_form_errors(),
            ["Number of submitted forms should be at most 1."],
        )
        self.assertEqual(
            str(formset.non_form_errors()),
            '<ul class="errorlist nonform">'
            "<li>Number of submitted forms should be at most 1.</li></ul>",
        )