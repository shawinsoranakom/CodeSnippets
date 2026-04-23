def test_error_list_with_non_field_errors_has_correct_class(self):
        class Person(Form):
            first_name = CharField()
            last_name = CharField()

            def clean(self):
                raise ValidationError("Generic validation error")

        p = Person({"first_name": "John", "last_name": "Lennon"})
        self.assertHTMLEqual(
            str(p.non_field_errors()),
            '<ul class="errorlist nonfield"><li>Generic validation error</li></ul>',
        )
        self.assertHTMLEqual(
            p.as_ul(),
            """<li>
<ul class="errorlist nonfield"><li>Generic validation error</li></ul></li>
<li><label for="id_first_name">First name:</label>
<input id="id_first_name" name="first_name" type="text" value="John" required></li>
<li><label for="id_last_name">Last name:</label>
<input id="id_last_name" name="last_name" type="text" value="Lennon" required></li>""",
        )
        self.assertHTMLEqual(
            p.non_field_errors().as_text(), "* Generic validation error"
        )
        self.assertHTMLEqual(
            p.as_p(),
            """<ul class="errorlist nonfield"><li>Generic validation error</li></ul>
<p><label for="id_first_name">First name:</label>
<input id="id_first_name" name="first_name" type="text" value="John" required></p>
<p><label for="id_last_name">Last name:</label>
<input id="id_last_name" name="last_name" type="text" value="Lennon" required></p>""",
        )
        self.assertHTMLEqual(
            p.as_table(),
            """
            <tr><td colspan="2"><ul class="errorlist nonfield">
            <li>Generic validation error</li></ul></td></tr>
            <tr><th><label for="id_first_name">First name:</label></th><td>
            <input id="id_first_name" name="first_name" type="text" value="John"
                required>
            </td></tr>
            <tr><th><label for="id_last_name">Last name:</label></th><td>
            <input id="id_last_name" name="last_name" type="text" value="Lennon"
                required>
            </td></tr>
            """,
        )
        self.assertHTMLEqual(
            p.as_div(),
            '<ul class="errorlist nonfield"><li>Generic validation error</li></ul>'
            '<div><label for="id_first_name">First name:</label><input '
            'id="id_first_name" name="first_name" type="text" value="John" required>'
            '</div><div><label for="id_last_name">Last name:</label><input '
            'id="id_last_name" name="last_name" type="text" value="Lennon" required>'
            "</div>",
        )