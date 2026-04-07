def test_blank_form_unfilled(self):
        """A form that's displayed as blank may be submitted as blank."""
        formset = self.make_choiceformset(
            [("Calexico", "100"), ("", "")], initial_forms=1
        )
        self.assertTrue(formset.is_valid())
        self.assertEqual(
            [form.cleaned_data for form in formset.forms],
            [{"votes": 100, "choice": "Calexico"}, {}],
        )