def test_ordering_blank_fieldsets(self):
        """Ordering works with blank fieldsets."""
        data = {
            "choices-TOTAL_FORMS": "3",  # the number of forms rendered
            "choices-INITIAL_FORMS": "0",  # the number of forms with initial data
            "choices-MIN_NUM_FORMS": "0",  # min number of forms
            "choices-MAX_NUM_FORMS": "0",  # max number of forms
        }
        ChoiceFormSet = formset_factory(Choice, can_order=True)
        formset = ChoiceFormSet(data, auto_id=False, prefix="choices")
        self.assertTrue(formset.is_valid())
        self.assertEqual(formset.ordered_forms, [])