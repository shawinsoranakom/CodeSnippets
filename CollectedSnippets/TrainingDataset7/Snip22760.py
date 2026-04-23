def test_auto_id(self):
        # "auto_id" tells the Form to add an "id" attribute to each form
        # element. If it's a string that contains '%s', Django will use that as
        # a format string into which the field's name will be inserted. It will
        # also put a <label> around the human-readable labels for a field.
        p = Person(auto_id="%s_id")
        self.assertHTMLEqual(
            p.as_table(),
            """<tr><th><label for="first_name_id">First name:</label></th><td>
<input type="text" name="first_name" id="first_name_id" required></td></tr>
<tr><th><label for="last_name_id">Last name:</label></th><td>
<input type="text" name="last_name" id="last_name_id" required></td></tr>
<tr><th><label for="birthday_id">Birthday:</label></th><td>
<input type="text" name="birthday" id="birthday_id" required></td></tr>""",
        )
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><label for="first_name_id">First name:</label>
<input type="text" name="first_name" id="first_name_id" required></li>
<li><label for="last_name_id">Last name:</label>
<input type="text" name="last_name" id="last_name_id" required></li>
<li><label for="birthday_id">Birthday:</label>
<input type="text" name="birthday" id="birthday_id" required></li>""",
        )
        self.assertHTMLEqual(
            p.as_p(),
            """<p><label for="first_name_id">First name:</label>
<input type="text" name="first_name" id="first_name_id" required></p>
<p><label for="last_name_id">Last name:</label>
<input type="text" name="last_name" id="last_name_id" required></p>
<p><label for="birthday_id">Birthday:</label>
<input type="text" name="birthday" id="birthday_id" required></p>""",
        )
        self.assertHTMLEqual(
            p.as_div(),
            '<div><label for="first_name_id">First name:</label><input type="text" '
            'name="first_name" id="first_name_id" required></div><div><label '
            'for="last_name_id">Last name:</label><input type="text" '
            'name="last_name" id="last_name_id" required></div><div><label '
            'for="birthday_id">Birthday:</label><input type="text" name="birthday" '
            'id="birthday_id" required></div>',
        )