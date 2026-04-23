def test_optional_data(self):
        # cleaned_data will include a key and value for *all* fields defined in
        # the Form, even if the Form's data didn't include a value for fields
        # that are not required. In this example, the data dictionary doesn't
        # include a value for the "nick_name" field, but cleaned_data includes
        # it. For CharFields, it's set to the empty string.
        class OptionalPersonForm(Form):
            first_name = CharField()
            last_name = CharField()
            nick_name = CharField(required=False)

        data = {"first_name": "John", "last_name": "Lennon"}
        f = OptionalPersonForm(data)
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data["nick_name"], "")
        self.assertEqual(f.cleaned_data["first_name"], "John")
        self.assertEqual(f.cleaned_data["last_name"], "Lennon")

        # For DateFields, it's set to None.
        class OptionalPersonForm(Form):
            first_name = CharField()
            last_name = CharField()
            birth_date = DateField(required=False)

        data = {"first_name": "John", "last_name": "Lennon"}
        f = OptionalPersonForm(data)
        self.assertTrue(f.is_valid())
        self.assertIsNone(f.cleaned_data["birth_date"])
        self.assertEqual(f.cleaned_data["first_name"], "John")
        self.assertEqual(f.cleaned_data["last_name"], "Lennon")