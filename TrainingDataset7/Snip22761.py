def test_auto_id_true(self):
        # If auto_id is any True value whose str() does not contain '%s', the
        # "id" attribute will be the name of the field.
        p = Person(auto_id=True)
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><label for="first_name">First name:</label>
<input type="text" name="first_name" id="first_name" required></li>
<li><label for="last_name">Last name:</label>
<input type="text" name="last_name" id="last_name" required></li>
<li><label for="birthday">Birthday:</label>
<input type="text" name="birthday" id="birthday" required></li>""",
        )