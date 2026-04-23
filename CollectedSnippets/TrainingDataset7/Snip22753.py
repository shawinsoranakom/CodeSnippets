def test_form(self):
        # Pass a dictionary to a Form's __init__().
        p = Person(
            {"first_name": "John", "last_name": "Lennon", "birthday": "1940-10-9"}
        )

        self.assertTrue(p.is_bound)
        self.assertEqual(p.errors, {})
        self.assertIsInstance(p.errors, dict)
        self.assertTrue(p.is_valid())
        self.assertHTMLEqual(p.errors.as_ul(), "")
        self.assertEqual(p.errors.as_text(), "")
        self.assertEqual(p.cleaned_data["first_name"], "John")
        self.assertEqual(p.cleaned_data["last_name"], "Lennon")
        self.assertEqual(p.cleaned_data["birthday"], datetime.date(1940, 10, 9))
        self.assertHTMLEqual(
            str(p["first_name"]),
            '<input type="text" name="first_name" value="John" id="id_first_name" '
            "required>",
        )
        self.assertHTMLEqual(
            str(p["last_name"]),
            '<input type="text" name="last_name" value="Lennon" id="id_last_name" '
            "required>",
        )
        self.assertHTMLEqual(
            str(p["birthday"]),
            '<input type="text" name="birthday" value="1940-10-9" id="id_birthday" '
            "required>",
        )

        msg = (
            "Key 'nonexistentfield' not found in 'Person'. Choices are: birthday, "
            "first_name, last_name."
        )
        with self.assertRaisesMessage(KeyError, msg):
            p["nonexistentfield"]

        form_output = []

        for boundfield in p:
            form_output.append(str(boundfield))

        self.assertHTMLEqual(
            "\n".join(form_output),
            '<input type="text" name="first_name" value="John" id="id_first_name" '
            "required>"
            '<input type="text" name="last_name" value="Lennon" id="id_last_name" '
            "required>"
            '<input type="text" name="birthday" value="1940-10-9" id="id_birthday" '
            "required>",
        )

        form_output = []

        for boundfield in p:
            form_output.append([boundfield.label, boundfield.data])

        self.assertEqual(
            form_output,
            [
                ["First name", "John"],
                ["Last name", "Lennon"],
                ["Birthday", "1940-10-9"],
            ],
        )
        self.assertHTMLEqual(
            str(p),
            '<div><label for="id_first_name">First name:</label><input type="text" '
            'name="first_name" value="John" required id="id_first_name"></div><div>'
            '<label for="id_last_name">Last name:</label><input type="text" '
            'name="last_name" value="Lennon" required id="id_last_name"></div><div>'
            '<label for="id_birthday">Birthday:</label><input type="text" '
            'name="birthday" value="1940-10-9" required id="id_birthday"></div>',
        )
        self.assertHTMLEqual(
            p.as_div(),
            '<div><label for="id_first_name">First name:</label><input type="text" '
            'name="first_name" value="John" required id="id_first_name"></div><div>'
            '<label for="id_last_name">Last name:</label><input type="text" '
            'name="last_name" value="Lennon" required id="id_last_name"></div><div>'
            '<label for="id_birthday">Birthday:</label><input type="text" '
            'name="birthday" value="1940-10-9" required id="id_birthday"></div>',
        )