def test_auto_id_false(self):
        # If auto_id is any False value, an "id" attribute won't be output
        # unless it was manually entered.
        p = Person(auto_id=False)
        self.assertHTMLEqual(
            p.as_ul(),
            """<li>First name: <input type="text" name="first_name" required></li>
<li>Last name: <input type="text" name="last_name" required></li>
<li>Birthday: <input type="text" name="birthday" required></li>""",
        )