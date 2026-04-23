def test_select_translated_text(self):
        # Deep copying translated text shouldn't raise an error.
        class CopyForm(Form):
            degree = IntegerField(widget=Select(choices=((1, gettext_lazy("test")),)))

        CopyForm()