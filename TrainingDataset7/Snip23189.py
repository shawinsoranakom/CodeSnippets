def test_html_rendering_of_prepopulated_models(self):
        none_model = ChoiceModel(name="none-test", choice_integer=None)
        f = EmptyIntegerLabelChoiceForm(instance=none_model)
        self.assertHTMLEqual(
            f.as_p(),
            """
            <p><label for="id_name">Name:</label>
            <input id="id_name" maxlength="10" name="name" type="text"
                value="none-test" required>
            </p>
            <p><label for="id_choice_integer">Choice integer:</label>
            <select id="id_choice_integer" name="choice_integer">
            <option value="" selected>No Preference</option>
            <option value="1">Foo</option>
            <option value="2">Bar</option>
            </select></p>
            """,
        )

        foo_model = ChoiceModel(name="foo-test", choice_integer=1)
        f = EmptyIntegerLabelChoiceForm(instance=foo_model)
        self.assertHTMLEqual(
            f.as_p(),
            """
            <p><label for="id_name">Name:</label>
            <input id="id_name" maxlength="10" name="name" type="text"
                value="foo-test" required>
            </p>
            <p><label for="id_choice_integer">Choice integer:</label>
            <select id="id_choice_integer" name="choice_integer">
            <option value="">No Preference</option>
            <option value="1" selected>Foo</option>
            <option value="2">Bar</option>
            </select></p>
            """,
        )