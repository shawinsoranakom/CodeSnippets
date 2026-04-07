def test_empty_field_char(self):
        f = EmptyCharLabelChoiceForm()
        self.assertHTMLEqual(
            f.as_p(),
            """
            <p><label for="id_name">Name:</label>
            <input id="id_name" maxlength="10" name="name" type="text" required></p>
            <p><label for="id_choice">Choice:</label>
            <select id="id_choice" name="choice">
            <option value="" selected>No Preference</option>
            <option value="f">Foo</option>
            <option value="b">Bar</option>
            </select></p>
            """,
        )