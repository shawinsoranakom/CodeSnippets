def test_empty_field_integer(self):
        f = EmptyIntegerLabelChoiceForm()
        self.assertHTMLEqual(
            f.as_p(),
            """
            <p><label for="id_name">Name:</label>
            <input id="id_name" maxlength="10" name="name" type="text" required></p>
            <p><label for="id_choice_integer">Choice integer:</label>
            <select id="id_choice_integer" name="choice_integer">
            <option value="" selected>No Preference</option>
            <option value="1">Foo</option>
            <option value="2">Bar</option>
            </select></p>
            """,
        )