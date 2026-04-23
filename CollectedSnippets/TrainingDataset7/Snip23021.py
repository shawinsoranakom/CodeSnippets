def test_formset_total_error_count(self):
        """A valid formset should have 0 total errors."""
        data = [  # formset_data, expected error count
            ([("Calexico", "100")], 0),
            ([("Calexico", "")], 1),
            ([("", "invalid")], 2),
            ([("Calexico", "100"), ("Calexico", "")], 1),
            ([("Calexico", ""), ("Calexico", "")], 2),
        ]
        for formset_data, expected_error_count in data:
            formset = self.make_choiceformset(formset_data)
            self.assertEqual(formset.total_error_count(), expected_error_count)