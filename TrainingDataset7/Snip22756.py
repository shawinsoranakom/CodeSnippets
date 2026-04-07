def test_unbound_form(self):
        # If you don't pass any values to the Form's __init__(), or if you pass
        # None, the Form will be considered unbound and won't do any
        # validation. Form.errors will be an empty dictionary *but*
        # Form.is_valid() will return False.
        p = Person()
        self.assertFalse(p.is_bound)
        self.assertEqual(p.errors, {})
        self.assertFalse(p.is_valid())
        with self.assertRaises(AttributeError):
            p.cleaned_data

        self.assertHTMLEqual(
            str(p),
            '<div><label for="id_first_name">First name:</label><input type="text" '
            'name="first_name" id="id_first_name" required></div><div><label '
            'for="id_last_name">Last name:</label><input type="text" name="last_name" '
            'id="id_last_name" required></div><div><label for="id_birthday">'
            'Birthday:</label><input type="text" name="birthday" id="id_birthday" '
            "required></div>",
        )
        self.assertHTMLEqual(
            p.as_table(),
            """<tr><th><label for="id_first_name">First name:</label></th><td>
<input type="text" name="first_name" id="id_first_name" required></td></tr>
<tr><th><label for="id_last_name">Last name:</label></th><td>
<input type="text" name="last_name" id="id_last_name" required></td></tr>
<tr><th><label for="id_birthday">Birthday:</label></th><td>
<input type="text" name="birthday" id="id_birthday" required></td></tr>""",
        )
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><label for="id_first_name">First name:</label>
<input type="text" name="first_name" id="id_first_name" required></li>
<li><label for="id_last_name">Last name:</label>
<input type="text" name="last_name" id="id_last_name" required></li>
<li><label for="id_birthday">Birthday:</label>
<input type="text" name="birthday" id="id_birthday" required></li>""",
        )
        self.assertHTMLEqual(
            p.as_p(),
            """<p><label for="id_first_name">First name:</label>
<input type="text" name="first_name" id="id_first_name" required></p>
<p><label for="id_last_name">Last name:</label>
<input type="text" name="last_name" id="id_last_name" required></p>
<p><label for="id_birthday">Birthday:</label>
<input type="text" name="birthday" id="id_birthday" required></p>""",
        )
        self.assertHTMLEqual(
            p.as_div(),
            '<div><label for="id_first_name">First name:</label><input type="text" '
            'name="first_name" id="id_first_name" required></div><div><label '
            'for="id_last_name">Last name:</label><input type="text" name="last_name" '
            'id="id_last_name" required></div><div><label for="id_birthday">'
            'Birthday:</label><input type="text" name="birthday" id="id_birthday" '
            "required></div>",
        )