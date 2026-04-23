def test_form_with_disabled_fields(self):
        class PersonForm(Form):
            name = CharField()
            birthday = DateField(disabled=True)

        class PersonFormFieldInitial(Form):
            name = CharField()
            birthday = DateField(disabled=True, initial=datetime.date(1974, 8, 16))

        # Disabled fields are generally not transmitted by user agents.
        # The value from the form's initial data is used.
        f1 = PersonForm(
            {"name": "John Doe"}, initial={"birthday": datetime.date(1974, 8, 16)}
        )
        f2 = PersonFormFieldInitial({"name": "John Doe"})
        for form in (f1, f2):
            self.assertTrue(form.is_valid())
            self.assertEqual(
                form.cleaned_data,
                {"birthday": datetime.date(1974, 8, 16), "name": "John Doe"},
            )

        # Values provided in the form's data are ignored.
        data = {"name": "John Doe", "birthday": "1984-11-10"}
        f1 = PersonForm(data, initial={"birthday": datetime.date(1974, 8, 16)})
        f2 = PersonFormFieldInitial(data)
        for form in (f1, f2):
            self.assertTrue(form.is_valid())
            self.assertEqual(
                form.cleaned_data,
                {"birthday": datetime.date(1974, 8, 16), "name": "John Doe"},
            )

        # Initial data remains present on invalid forms.
        data = {}
        f1 = PersonForm(data, initial={"birthday": datetime.date(1974, 8, 16)})
        f2 = PersonFormFieldInitial(data)
        for form in (f1, f2):
            self.assertFalse(form.is_valid())
            self.assertEqual(form["birthday"].value(), datetime.date(1974, 8, 16))