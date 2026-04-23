def test_id_on_field(self):
        # In this example, auto_id is False, but the "id" attribute for the
        # "first_name" field is given. Also note that field gets a <label>,
        # while the others don't.
        p = PersonNew(auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><label for="first_name_id">First name:</label>
<input type="text" id="first_name_id" name="first_name" required></li>
<li>Last name: <input type="text" name="last_name" required></li>
<li>Birthday: <input type="text" name="birthday" required></li>""",
        )