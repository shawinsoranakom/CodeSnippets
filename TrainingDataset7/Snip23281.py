def test_fieldset(self):
        class TestForm(Form):
            template_name = "forms_tests/use_fieldset.html"
            composers = MultipleChoiceField(
                choices=[("J", "John Lennon"), ("P", "Paul McCartney")],
                widget=MultipleHiddenInput,
            )

        form = TestForm(MultiValueDict({"composers": ["J", "P"]}))
        self.assertIs(self.widget.use_fieldset, False)
        self.assertHTMLEqual(
            '<input type="hidden" name="composers" value="J" id="id_composers_0">'
            '<input type="hidden" name="composers" value="P" id="id_composers_1">',
            form.render(),
        )