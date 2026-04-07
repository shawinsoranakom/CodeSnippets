def test_cleaned_data_only_fields(self):
        # cleaned_data will always *only* contain a key for fields defined in
        # the Form, even if you pass extra data when you define the Form. In
        # this example, we pass a bunch of extra fields to the form
        # constructor, but cleaned_data contains only the form's fields.
        data = {
            "first_name": "John",
            "last_name": "Lennon",
            "birthday": "1940-10-9",
            "extra1": "hello",
            "extra2": "hello",
        }
        p = Person(data)
        self.assertTrue(p.is_valid())
        self.assertEqual(p.cleaned_data["first_name"], "John")
        self.assertEqual(p.cleaned_data["last_name"], "Lennon")
        self.assertEqual(p.cleaned_data["birthday"], datetime.date(1940, 10, 9))