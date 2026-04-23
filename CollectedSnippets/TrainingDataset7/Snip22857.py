def test_error_list_with_hidden_field_errors_has_correct_class(self):
        class Person(Form):
            first_name = CharField()
            last_name = CharField(widget=HiddenInput)

        p = Person({"first_name": "John"})
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><ul class="errorlist nonfield">
<li>(Hidden field last_name) This field is required.</li></ul></li><li>
<label for="id_first_name">First name:</label>
<input id="id_first_name" name="first_name" type="text" value="John" required>
<input id="id_last_name" name="last_name" type="hidden"></li>""",
        )
        self.assertHTMLEqual(
            p.as_p(),
            """
            <ul class="errorlist nonfield">
            <li>(Hidden field last_name) This field is required.</li></ul>
            <p><label for="id_first_name">First name:</label>
            <input id="id_first_name" name="first_name" type="text" value="John"
                required>
            <input id="id_last_name" name="last_name" type="hidden"></p>
            """,
        )
        self.assertHTMLEqual(
            p.as_table(),
            """<tr><td colspan="2"><ul class="errorlist nonfield">
<li>(Hidden field last_name) This field is required.</li></ul></td></tr>
<tr><th><label for="id_first_name">First name:</label></th><td>
<input id="id_first_name" name="first_name" type="text" value="John" required>
<input id="id_last_name" name="last_name" type="hidden"></td></tr>""",
        )
        self.assertHTMLEqual(
            p.as_div(),
            '<ul class="errorlist nonfield"><li>(Hidden field last_name) This field '
            'is required.</li></ul><div><label for="id_first_name">First name:</label>'
            '<input id="id_first_name" name="first_name" type="text" value="John" '
            'required><input id="id_last_name" name="last_name" type="hidden"></div>',
        )