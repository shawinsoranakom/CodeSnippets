def test_empty_fields_on_modelformset(self):
        """
        No fields passed to modelformset_factory() should result in no fields
        on returned forms except for the id (#14119).
        """
        UserFormSet = modelformset_factory(User, fields=())
        formset = UserFormSet()
        for form in formset.forms:
            self.assertIn("id", form.fields)
            self.assertEqual(len(form.fields), 1)