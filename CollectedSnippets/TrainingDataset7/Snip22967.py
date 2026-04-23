def test_formset_validation(self):
        # FormSet instances can also have an error attribute if validation
        # failed for any of the forms.
        formset = self.make_choiceformset([("Calexico", "")])
        self.assertFalse(formset.is_valid())
        self.assertEqual(formset.errors, [{"votes": ["This field is required."]}])