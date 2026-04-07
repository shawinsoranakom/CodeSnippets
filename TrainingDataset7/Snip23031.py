def test_repr(self):
        valid_formset = self.make_choiceformset([("test", 1)])
        valid_formset.full_clean()
        invalid_formset = self.make_choiceformset([("test", "")])
        invalid_formset.full_clean()
        partially_invalid_formset = self.make_choiceformset(
            [("test", "1"), ("test", "")],
        )
        partially_invalid_formset.full_clean()
        invalid_formset_non_form_errors_only = self.make_choiceformset(
            [("test", "")],
            formset_class=ChoiceFormsetWithNonFormError,
        )
        invalid_formset_non_form_errors_only.full_clean()

        cases = [
            (
                self.make_choiceformset(),
                "<ChoiceFormSet: bound=False valid=Unknown total_forms=1>",
            ),
            (
                self.make_choiceformset(
                    formset_class=formset_factory(Choice, extra=10),
                ),
                "<ChoiceFormSet: bound=False valid=Unknown total_forms=10>",
            ),
            (
                self.make_choiceformset([]),
                "<ChoiceFormSet: bound=True valid=Unknown total_forms=0>",
            ),
            (
                self.make_choiceformset([("test", 1)]),
                "<ChoiceFormSet: bound=True valid=Unknown total_forms=1>",
            ),
            (valid_formset, "<ChoiceFormSet: bound=True valid=True total_forms=1>"),
            (invalid_formset, "<ChoiceFormSet: bound=True valid=False total_forms=1>"),
            (
                partially_invalid_formset,
                "<ChoiceFormSet: bound=True valid=False total_forms=2>",
            ),
            (
                invalid_formset_non_form_errors_only,
                "<ChoiceFormsetWithNonFormError: bound=True valid=False total_forms=1>",
            ),
        ]
        for formset, expected_repr in cases:
            with self.subTest(expected_repr=expected_repr):
                self.assertEqual(repr(formset), expected_repr)