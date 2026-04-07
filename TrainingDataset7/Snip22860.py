def test_baseform_repr(self):
        """
        BaseForm.__repr__() should contain some basic information about the
        form.
        """
        p = Person()
        self.assertEqual(
            repr(p),
            "<Person bound=False, valid=Unknown, "
            "fields=(first_name;last_name;birthday)>",
        )
        p = Person(
            {"first_name": "John", "last_name": "Lennon", "birthday": "1940-10-9"}
        )
        self.assertEqual(
            repr(p),
            "<Person bound=True, valid=Unknown, "
            "fields=(first_name;last_name;birthday)>",
        )
        p.is_valid()
        self.assertEqual(
            repr(p),
            "<Person bound=True, valid=True, fields=(first_name;last_name;birthday)>",
        )
        p = Person(
            {"first_name": "John", "last_name": "Lennon", "birthday": "fakedate"}
        )
        p.is_valid()
        self.assertEqual(
            repr(p),
            "<Person bound=True, valid=False, fields=(first_name;last_name;birthday)>",
        )