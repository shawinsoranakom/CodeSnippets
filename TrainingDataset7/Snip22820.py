def test_fieldset_custom_aria_describedby(self):
        # aria-describedby set on widget results in aria-describedby being
        # added to widget and not the <fieldset>.
        class FieldsetForm(Form):
            checkbox = MultipleChoiceField(
                choices=[("a", "A"), ("b", "B")],
                widget=CheckboxSelectMultiple(attrs={"aria-describedby": "custom-id"}),
                help_text="Checkbox help text",
            )

        f = FieldsetForm()
        self.assertHTMLEqual(
            str(f),
            "<div><fieldset><legend>Checkbox:</legend>"
            '<div class="helptext" id="id_checkbox_helptext">Checkbox help text</div>'
            '<div id="id_checkbox"><div>'
            '<label for="id_checkbox_0"><input type="checkbox" name="checkbox" '
            'value="a" aria-describedby="custom-id" id="id_checkbox_0" />A</label>'
            "</div><div>"
            '<label for="id_checkbox_1"><input type="checkbox" name="checkbox" '
            'value="b" aria-describedby="custom-id" id="id_checkbox_1" />B</label>'
            "</div></div></fieldset></div>",
        )