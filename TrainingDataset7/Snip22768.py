def test_forms_with_radio(self):
        # Add widget=RadioSelect to use that widget with a ChoiceField.
        f = FrameworkForm(auto_id=False)
        self.assertHTMLEqual(
            str(f["language"]),
            """<div>
<div><label><input type="radio" name="language" value="P" required> Python</label></div>
<div><label><input type="radio" name="language" value="J" required> Java</label></div>
</div>""",
        )
        self.assertHTMLEqual(
            f.as_table(),
            """<tr><th>Name:</th><td><input type="text" name="name" required></td></tr>
<tr><th>Language:</th><td><div>
<div><label><input type="radio" name="language" value="P" required> Python</label></div>
<div><label><input type="radio" name="language" value="J" required> Java</label></div>
</div></td></tr>""",
        )
        self.assertHTMLEqual(
            f.as_ul(),
            """<li>Name: <input type="text" name="name" required></li>
<li>Language: <div>
<div><label><input type="radio" name="language" value="P" required> Python</label></div>
<div><label><input type="radio" name="language" value="J" required> Java</label></div>
</div></li>""",
        )
        # Need an auto_id to generate legend.
        self.assertHTMLEqual(
            f.render(f.template_name_div),
            '<div> Name: <input type="text" name="name" required></div><div><fieldset>'
            'Language:<div><div><label><input type="radio" name="language" value="P" '
            'required> Python</label></div><div><label><input type="radio" '
            'name="language" value="J" required> Java</label></div></div></fieldset>'
            "</div>",
        )

        # Regarding auto_id and <label>, RadioSelect is a special case. Each
        # radio button gets a distinct ID, formed by appending an underscore
        # plus the button's zero-based index.
        f = FrameworkForm(auto_id="id_%s")
        self.assertHTMLEqual(
            str(f["language"]),
            """
            <div id="id_language">
            <div><label for="id_language_0">
            <input type="radio" id="id_language_0" value="P" name="language" required>
            Python</label></div>
            <div><label for="id_language_1">
            <input type="radio" id="id_language_1" value="J" name="language" required>
            Java</label></div>
            </div>""",
        )

        # When RadioSelect is used with auto_id, and the whole form is printed
        # using either as_table() or as_ul(), the label for the RadioSelect
        # will **not** point to the ID of the *first* radio button to improve
        # accessibility for screen reader users.
        self.assertHTMLEqual(
            f.as_table(),
            """
            <tr><th><label for="id_name">Name:</label></th><td>
            <input type="text" name="name" id="id_name" required></td></tr>
            <tr><th><label>Language:</label></th><td><div id="id_language">
            <div><label for="id_language_0">
            <input type="radio" id="id_language_0" value="P" name="language" required>
            Python</label></div>
            <div><label for="id_language_1">
            <input type="radio" id="id_language_1" value="J" name="language" required>
            Java</label></div>
            </div></td></tr>""",
        )
        self.assertHTMLEqual(
            f.as_ul(),
            """
            <li><label for="id_name">Name:</label>
            <input type="text" name="name" id="id_name" required></li>
            <li><label>Language:</label> <div id="id_language">
            <div><label for="id_language_0">
            <input type="radio" id="id_language_0" value="P" name="language" required>
            Python</label></div>
            <div><label for="id_language_1">
            <input type="radio" id="id_language_1" value="J" name="language" required>
            Java</label></div>
            </div></li>
            """,
        )
        self.assertHTMLEqual(
            f.as_p(),
            """
            <p><label for="id_name">Name:</label>
            <input type="text" name="name" id="id_name" required></p>
            <p><label>Language:</label> <div id="id_language">
            <div><label for="id_language_0">
            <input type="radio" id="id_language_0" value="P" name="language" required>
            Python</label></div>
            <div><label for="id_language_1">
            <input type="radio" id="id_language_1" value="J" name="language" required>
            Java</label></div>
            </div></p>
            """,
        )
        self.assertHTMLEqual(
            f.render(f.template_name_div),
            '<div><label for="id_name">Name:</label><input type="text" name="name" '
            'required id="id_name"></div><div><fieldset><legend>Language:</legend>'
            '<div id="id_language"><div><label for="id_language_0"><input '
            'type="radio" name="language" value="P" required id="id_language_0">'
            'Python</label></div><div><label for="id_language_1"><input type="radio" '
            'name="language" value="J" required id="id_language_1">Java</label></div>'
            "</div></fieldset></div>",
        )