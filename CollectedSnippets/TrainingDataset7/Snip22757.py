def test_unicode_values(self):
        # Unicode values are handled properly.
        p = Person(
            {
                "first_name": "John",
                "last_name": "\u0160\u0110\u0106\u017d\u0107\u017e\u0161\u0111",
                "birthday": "1940-10-9",
            }
        )
        self.assertHTMLEqual(
            p.as_table(),
            '<tr><th><label for="id_first_name">First name:</label></th><td>'
            '<input type="text" name="first_name" value="John" id="id_first_name" '
            "required></td></tr>\n"
            '<tr><th><label for="id_last_name">Last name:</label>'
            '</th><td><input type="text" name="last_name" '
            'value="\u0160\u0110\u0106\u017d\u0107\u017e\u0161\u0111"'
            'id="id_last_name" required></td></tr>\n'
            '<tr><th><label for="id_birthday">Birthday:</label></th><td>'
            '<input type="text" name="birthday" value="1940-10-9" id="id_birthday" '
            "required></td></tr>",
        )
        self.assertHTMLEqual(
            p.as_ul(),
            '<li><label for="id_first_name">First name:</label> '
            '<input type="text" name="first_name" value="John" id="id_first_name" '
            "required></li>\n"
            '<li><label for="id_last_name">Last name:</label> '
            '<input type="text" name="last_name" '
            'value="\u0160\u0110\u0106\u017d\u0107\u017e\u0161\u0111" '
            'id="id_last_name" required></li>\n'
            '<li><label for="id_birthday">Birthday:</label> '
            '<input type="text" name="birthday" value="1940-10-9" id="id_birthday" '
            "required></li>",
        )
        self.assertHTMLEqual(
            p.as_p(),
            '<p><label for="id_first_name">First name:</label> '
            '<input type="text" name="first_name" value="John" id="id_first_name" '
            "required></p>\n"
            '<p><label for="id_last_name">Last name:</label> '
            '<input type="text" name="last_name" '
            'value="\u0160\u0110\u0106\u017d\u0107\u017e\u0161\u0111" '
            'id="id_last_name" required></p>\n'
            '<p><label for="id_birthday">Birthday:</label> '
            '<input type="text" name="birthday" value="1940-10-9" id="id_birthday" '
            "required></p>",
        )
        self.assertHTMLEqual(
            p.as_div(),
            '<div><label for="id_first_name">First name:</label>'
            '<input type="text" name="first_name" value="John" id="id_first_name" '
            'required></div><div><label for="id_last_name">Last name:</label>'
            '<input type="text" name="last_name"'
            'value="\u0160\u0110\u0106\u017d\u0107\u017e\u0161\u0111" '
            'id="id_last_name" required></div><div><label for="id_birthday">'
            'Birthday:</label><input type="text" name="birthday" value="1940-10-9" '
            'id="id_birthday" required></div>',
        )

        p = Person({"last_name": "Lennon"})
        self.assertEqual(p.errors["first_name"], ["This field is required."])
        self.assertEqual(p.errors["birthday"], ["This field is required."])
        self.assertFalse(p.is_valid())
        self.assertEqual(
            p.errors,
            {
                "birthday": ["This field is required."],
                "first_name": ["This field is required."],
            },
        )
        self.assertEqual(p.cleaned_data, {"last_name": "Lennon"})
        self.assertEqual(p["first_name"].errors, ["This field is required."])
        self.assertHTMLEqual(
            p["first_name"].errors.as_ul(),
            '<ul class="errorlist" id="id_first_name_error">'
            "<li>This field is required.</li></ul>",
        )
        self.assertEqual(p["first_name"].errors.as_text(), "* This field is required.")

        p = Person()
        self.assertHTMLEqual(
            str(p["first_name"]),
            '<input type="text" name="first_name" id="id_first_name" required>',
        )
        self.assertHTMLEqual(
            str(p["last_name"]),
            '<input type="text" name="last_name" id="id_last_name" required>',
        )
        self.assertHTMLEqual(
            str(p["birthday"]),
            '<input type="text" name="birthday" id="id_birthday" required>',
        )