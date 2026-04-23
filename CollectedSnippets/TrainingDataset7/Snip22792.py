def test_hidden_widget_does_not_have_aria_describedby(self):
        class TestForm(Form):
            hidden_text = CharField(widget=HiddenInput, help_text="Help Text")

        f = TestForm()
        self.assertEqual(
            str(f), '<input type="hidden" name="hidden_text" id="id_hidden_text">'
        )