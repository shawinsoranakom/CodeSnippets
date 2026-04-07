def test_boundfield_bool(self):
        """BoundField without any choices (subwidgets) evaluates to True."""

        class TestForm(Form):
            name = ChoiceField(choices=[])

        self.assertIs(bool(TestForm()["name"]), True)