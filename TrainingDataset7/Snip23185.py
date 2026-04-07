def test_empty_field_char_none(self):
        f = EmptyCharLabelNoneChoiceForm()
        self.assertHTMLEqual(
            f.as_p(),
            """
            <p><label for="id_name">Name:</label>
            <input id="id_name" maxlength="10" name="name" type="text" required></p>
            <p><label for="id_choice_string_w_none">Choice string w none:</label>
            <select id="id_choice_string_w_none" name="choice_string_w_none">
            <option value="" selected>No Preference</option>
            <option value="f">Foo</option>
            <option value="b">Bar</option>
            </select></p>
            """,
        )