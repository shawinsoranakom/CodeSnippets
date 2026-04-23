def test_hidden_widget(self):
        # HiddenInput widgets are displayed differently in the as_table(),
        # as_ul()) and as_p() output of a Form -- their verbose names are not
        # displayed, and a separate row is not displayed. They're displayed in
        # the last row of the form, directly after that row's form element.
        class Person(Form):
            first_name = CharField()
            last_name = CharField()
            hidden_text = CharField(widget=HiddenInput)
            birthday = DateField()

        p = Person(auto_id=False)
        self.assertHTMLEqual(
            p.as_table(),
            """
            <tr><th>First name:</th><td><input type="text" name="first_name" required>
            </td></tr>
            <tr><th>Last name:</th><td><input type="text" name="last_name" required>
            </td></tr>
            <tr><th>Birthday:</th>
            <td><input type="text" name="birthday" required>
            <input type="hidden" name="hidden_text"></td></tr>
            """,
        )
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li>First name: <input type="text" name="first_name" required></li>
            <li>Last name: <input type="text" name="last_name" required></li>
            <li>Birthday: <input type="text" name="birthday" required>
            <input type="hidden" name="hidden_text"></li>
            """,
        )
        self.assertHTMLEqual(
            p.as_p(),
            """
            <p>First name: <input type="text" name="first_name" required></p>
            <p>Last name: <input type="text" name="last_name" required></p>
            <p>Birthday: <input type="text" name="birthday" required>
            <input type="hidden" name="hidden_text"></p>
            """,
        )
        self.assertHTMLEqual(
            p.as_div(),
            '<div>First name: <input type="text" name="first_name" required></div>'
            '<div>Last name: <input type="text" name="last_name" required></div><div>'
            'Birthday: <input type="text" name="birthday" required><input '
            'type="hidden" name="hidden_text"></div>',
        )

        # With auto_id set, a HiddenInput still gets an ID, but it doesn't get
        # a label.
        p = Person(auto_id="id_%s")
        self.assertHTMLEqual(
            p.as_table(),
            """<tr><th><label for="id_first_name">First name:</label></th><td>
<input type="text" name="first_name" id="id_first_name" required></td></tr>
<tr><th><label for="id_last_name">Last name:</label></th><td>
<input type="text" name="last_name" id="id_last_name" required></td></tr>
<tr><th><label for="id_birthday">Birthday:</label></th><td>
<input type="text" name="birthday" id="id_birthday" required>
<input type="hidden" name="hidden_text" id="id_hidden_text"></td></tr>""",
        )
        self.assertHTMLEqual(
            p.as_ul(),
            """<li><label for="id_first_name">First name:</label>
<input type="text" name="first_name" id="id_first_name" required></li>
<li><label for="id_last_name">Last name:</label>
<input type="text" name="last_name" id="id_last_name" required></li>
<li><label for="id_birthday">Birthday:</label>
<input type="text" name="birthday" id="id_birthday" required>
<input type="hidden" name="hidden_text" id="id_hidden_text"></li>""",
        )
        self.assertHTMLEqual(
            p.as_p(),
            """<p><label for="id_first_name">First name:</label>
<input type="text" name="first_name" id="id_first_name" required></p>
<p><label for="id_last_name">Last name:</label>
<input type="text" name="last_name" id="id_last_name" required></p>
<p><label for="id_birthday">Birthday:</label>
<input type="text" name="birthday" id="id_birthday" required>
<input type="hidden" name="hidden_text" id="id_hidden_text"></p>""",
        )
        self.assertHTMLEqual(
            p.as_div(),
            '<div><label for="id_first_name">First name:</label><input type="text" '
            'name="first_name" id="id_first_name" required></div><div><label '
            'for="id_last_name">Last name:</label><input type="text" name="last_name" '
            'id="id_last_name" required></div><div><label for="id_birthday">Birthday:'
            '</label><input type="text" name="birthday" id="id_birthday" required>'
            '<input type="hidden" name="hidden_text" id="id_hidden_text"></div>',
        )

        # If a field with a HiddenInput has errors, the as_table() and as_ul()
        # output will include the error message(s) with the text "(Hidden field
        # [fieldname]) " prepended. This message is displayed at the top of the
        # output, regardless of its field's order in the form.
        p = Person(
            {"first_name": "John", "last_name": "Lennon", "birthday": "1940-10-9"},
            auto_id=False,
        )
        self.assertHTMLEqual(
            p.as_table(),
            """
            <tr><td colspan="2">
            <ul class="errorlist nonfield"><li>
            (Hidden field hidden_text) This field is required.</li></ul></td></tr>
            <tr><th>First name:</th><td>
            <input type="text" name="first_name" value="John" required></td></tr>
            <tr><th>Last name:</th><td>
            <input type="text" name="last_name" value="Lennon" required></td></tr>
            <tr><th>Birthday:</th><td>
            <input type="text" name="birthday" value="1940-10-9" required>
            <input type="hidden" name="hidden_text"></td></tr>
            """,
        )
        self.assertHTMLEqual(
            p.as_ul(),
            """
            <li><ul class="errorlist nonfield"><li>
            (Hidden field hidden_text) This field is required.</li></ul></li>
            <li>First name: <input type="text" name="first_name" value="John" required>
            </li>
            <li>Last name: <input type="text" name="last_name" value="Lennon" required>
            </li>
            <li>Birthday: <input type="text" name="birthday" value="1940-10-9" required>
            <input type="hidden" name="hidden_text"></li>
            """,
        )
        self.assertHTMLEqual(
            p.as_p(),
            """
            <ul class="errorlist nonfield"><li>
            (Hidden field hidden_text) This field is required.</li></ul>
            <p>First name: <input type="text" name="first_name" value="John" required>
            </p>
            <p>Last name: <input type="text" name="last_name" value="Lennon" required>
            </p>
            <p>Birthday: <input type="text" name="birthday" value="1940-10-9" required>
            <input type="hidden" name="hidden_text"></p>
            """,
        )
        self.assertHTMLEqual(
            p.as_div(),
            '<ul class="errorlist nonfield"><li>(Hidden field hidden_text) This field '
            'is required.</li></ul><div>First name: <input type="text" '
            'name="first_name" value="John" required></div><div>Last name: <input '
            'type="text" name="last_name" value="Lennon" required></div><div>'
            'Birthday: <input type="text" name="birthday" value="1940-10-9" required>'
            '<input type="hidden" name="hidden_text"></div>',
        )

        # A corner case: It's possible for a form to have only HiddenInputs.
        class TestForm(Form):
            foo = CharField(widget=HiddenInput)
            bar = CharField(widget=HiddenInput)

        p = TestForm(auto_id=False)
        self.assertHTMLEqual(
            p.as_table(),
            '<input type="hidden" name="foo"><input type="hidden" name="bar">',
        )
        self.assertHTMLEqual(
            p.as_ul(),
            '<input type="hidden" name="foo"><input type="hidden" name="bar">',
        )
        self.assertHTMLEqual(
            p.as_p(), '<input type="hidden" name="foo"><input type="hidden" name="bar">'
        )