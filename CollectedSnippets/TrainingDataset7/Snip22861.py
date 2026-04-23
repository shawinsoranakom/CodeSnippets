def test_baseform_repr_dont_trigger_validation(self):
        """
        BaseForm.__repr__() shouldn't trigger the form validation.
        """
        p = Person(
            {"first_name": "John", "last_name": "Lennon", "birthday": "fakedate"}
        )
        repr(p)
        with self.assertRaises(AttributeError):
            p.cleaned_data
        self.assertFalse(p.is_valid())
        self.assertEqual(p.cleaned_data, {"first_name": "John", "last_name": "Lennon"})