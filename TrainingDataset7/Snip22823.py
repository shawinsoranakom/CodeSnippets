def test_forms_with_prefixes(self):
        # Sometimes it's necessary to have multiple forms display on the same
        # HTML page, or multiple copies of the same form. We can accomplish
        # this with form prefixes. Pass the keyword argument 'prefix' to the
        # Form constructor to use this feature. This value will be prepended to
        # each HTML form field name. One way to think about this is "namespaces
        # for HTML forms". Notice that in the data argument, each field's key
        # has the prefix, in this case 'person1', prepended to the actual field
        # name.
        class Person(Form):
            first_name = CharField()
            last_name = CharField()
            birthday = DateField()

        data = {
            "person1-first_name": "John",
            "person1-last_name": "Lennon",
            "person1-birthday": "1940-10-9",
        }
        p = Person(data, prefix="person1")
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li><label for="id_person1-first_name">First name:</label>
            <input type="text" name="person1-first_name" value="John"
                id="id_person1-first_name" required></li>
            <li><label for="id_person1-last_name">Last name:</label>
            <input type="text" name="person1-last_name" value="Lennon"
                id="id_person1-last_name" required></li>
            <li><label for="id_person1-birthday">Birthday:</label>
            <input type="text" name="person1-birthday" value="1940-10-9"
                id="id_person1-birthday" required></li>
            """,
        )
        self.assertHTMLEqual(
            str(p["first_name"]),
            '<input type="text" name="person1-first_name" value="John" '
            'id="id_person1-first_name" required>',
        )
        self.assertHTMLEqual(
            str(p["last_name"]),
            '<input type="text" name="person1-last_name" value="Lennon" '
            'id="id_person1-last_name" required>',
        )
        self.assertHTMLEqual(
            str(p["birthday"]),
            '<input type="text" name="person1-birthday" value="1940-10-9" '
            'id="id_person1-birthday" required>',
        )
        self.assertEqual(p.errors, {})
        self.assertTrue(p.is_valid())
        self.assertEqual(p.cleaned_data["first_name"], "John")
        self.assertEqual(p.cleaned_data["last_name"], "Lennon")
        self.assertEqual(p.cleaned_data["birthday"], datetime.date(1940, 10, 9))

        # Let's try submitting some bad data to make sure form.errors and
        # field.errors work as expected.
        data = {
            "person1-first_name": "",
            "person1-last_name": "",
            "person1-birthday": "",
        }
        p = Person(data, prefix="person1")
        self.assertEqual(p.errors["first_name"], ["This field is required."])
        self.assertEqual(p.errors["last_name"], ["This field is required."])
        self.assertEqual(p.errors["birthday"], ["This field is required."])
        self.assertEqual(p["first_name"].errors, ["This field is required."])
        # Accessing a nonexistent field.
        with self.assertRaises(KeyError):
            p["person1-first_name"].errors

        # In this example, the data doesn't have a prefix, but the form
        # requires it, so the form doesn't "see" the fields.
        data = {"first_name": "John", "last_name": "Lennon", "birthday": "1940-10-9"}
        p = Person(data, prefix="person1")
        self.assertEqual(p.errors["first_name"], ["This field is required."])
        self.assertEqual(p.errors["last_name"], ["This field is required."])
        self.assertEqual(p.errors["birthday"], ["This field is required."])

        # With prefixes, a single data dictionary can hold data for multiple
        # instances of the same form.
        data = {
            "person1-first_name": "John",
            "person1-last_name": "Lennon",
            "person1-birthday": "1940-10-9",
            "person2-first_name": "Jim",
            "person2-last_name": "Morrison",
            "person2-birthday": "1943-12-8",
        }
        p1 = Person(data, prefix="person1")
        self.assertTrue(p1.is_valid())
        self.assertEqual(p1.cleaned_data["first_name"], "John")
        self.assertEqual(p1.cleaned_data["last_name"], "Lennon")
        self.assertEqual(p1.cleaned_data["birthday"], datetime.date(1940, 10, 9))
        p2 = Person(data, prefix="person2")
        self.assertTrue(p2.is_valid())
        self.assertEqual(p2.cleaned_data["first_name"], "Jim")
        self.assertEqual(p2.cleaned_data["last_name"], "Morrison")
        self.assertEqual(p2.cleaned_data["birthday"], datetime.date(1943, 12, 8))

        # By default, forms append a hyphen between the prefix and the field
        # name, but a form can alter that behavior by implementing the
        # add_prefix() method. This method takes a field name and returns the
        # prefixed field, according to self.prefix.
        class Person(Form):
            first_name = CharField()
            last_name = CharField()
            birthday = DateField()

            def add_prefix(self, field_name):
                return (
                    "%s-prefix-%s" % (self.prefix, field_name)
                    if self.prefix
                    else field_name
                )

        p = Person(prefix="foo")
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li><label for="id_foo-prefix-first_name">First name:</label>
            <input type="text" name="foo-prefix-first_name"
                id="id_foo-prefix-first_name" required></li>
            <li><label for="id_foo-prefix-last_name">Last name:</label>
            <input type="text" name="foo-prefix-last_name" id="id_foo-prefix-last_name"
                required></li>
            <li><label for="id_foo-prefix-birthday">Birthday:</label>
            <input type="text" name="foo-prefix-birthday" id="id_foo-prefix-birthday"
                required></li>
            """,
        )
        data = {
            "foo-prefix-first_name": "John",
            "foo-prefix-last_name": "Lennon",
            "foo-prefix-birthday": "1940-10-9",
        }
        p = Person(data, prefix="foo")
        self.assertTrue(p.is_valid())
        self.assertEqual(p.cleaned_data["first_name"], "John")
        self.assertEqual(p.cleaned_data["last_name"], "Lennon")
        self.assertEqual(p.cleaned_data["birthday"], datetime.date(1940, 10, 9))