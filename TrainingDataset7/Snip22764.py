def test_auto_id_on_form_and_field(self):
        # If the "id" attribute is specified in the Form and auto_id is True,
        # the "id" attribute in the Form gets precedence.
        p = PersonNew(auto_id=True)
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><label for="first_name_id">First name:</label>
<input type="text" id="first_name_id" name="first_name" required></li>
<li><label for="last_name">Last name:</label>
<input type="text" name="last_name" id="last_name" required></li>
<li><label for="birthday">Birthday:</label>
<input type="text" name="birthday" id="birthday" required></li>""",
        )