def test_fieldset_aria_describedby(self):
        class FieldsetForm(Form):
            checkbox = MultipleChoiceField(
                choices=[("a", "A"), ("b", "B")],
                widget=CheckboxSelectMultiple,
                help_text="Checkbox help text",
            )
            radio = MultipleChoiceField(
                choices=[("a", "A"), ("b", "B")],
                widget=RadioSelect,
                help_text="Radio help text",
            )
            datetime = SplitDateTimeField(help_text="Enter Date and Time")

        f = FieldsetForm()
        self.assertHTMLEqual(
            str(f),
            '<div><fieldset aria-describedby="id_checkbox_helptext">'
            "<legend>Checkbox:</legend>"
            '<div class="helptext" id="id_checkbox_helptext">Checkbox help text</div>'
            '<div id="id_checkbox"><div>'
            '<label for="id_checkbox_0"><input type="checkbox" name="checkbox" '
            'value="a" id="id_checkbox_0" /> A</label>'
            "</div><div>"
            '<label for="id_checkbox_1"><input type="checkbox" name="checkbox" '
            'value="b" id="id_checkbox_1" /> B</label>'
            "</div></div></fieldset></div>"
            '<div><fieldset aria-describedby="id_radio_helptext">'
            "<legend>Radio:</legend>"
            '<div class="helptext" id="id_radio_helptext">Radio help text</div>'
            '<div id="id_radio"><div>'
            '<label for="id_radio_0"><input type="radio" name="radio" value="a" '
            'required id="id_radio_0" />A</label>'
            "</div><div>"
            '<label for="id_radio_1"><input type="radio" name="radio" value="b" '
            'required id="id_radio_1" /> B</label>'
            "</div></div></fieldset></div>"
            '<div><fieldset aria-describedby="id_datetime_helptext">'
            "<legend>Datetime:</legend>"
            '<div class="helptext" id="id_datetime_helptext">Enter Date and Time</div>'
            '<input type="text" name="datetime_0" required id="id_datetime_0" />'
            '<input type="text" name="datetime_1" required id="id_datetime_1" />'
            "</fieldset></div>",
        )
        f = FieldsetForm({})
        self.assertHTMLEqual(
            '<div><fieldset aria-describedby="id_checkbox_helptext '
            'id_checkbox_error"> <legend>Checkbox:</legend> <div class="helptext" '
            'id="id_checkbox_helptext">Checkbox help text</div> <ul class="errorlist" '
            'id="id_checkbox_error"> <li>This field is required.</li> </ul> '
            '<div id="id_checkbox"> <div> <label for="id_checkbox_0"><input '
            'type="checkbox" name="checkbox" value="a" aria-invalid="true" '
            'id="id_checkbox_0" /> A</label> </div> <div> <label for="id_checkbox_1">'
            '<input type="checkbox" name="checkbox" value="b" aria-invalid="true" '
            'id="id_checkbox_1" /> B</label> </div> </div> </fieldset> </div> <div> '
            '<fieldset aria-describedby="id_radio_helptext id_radio_error"> '
            '<legend>Radio:</legend> <div class="helptext" id="id_radio_helptext">'
            'Radio help text</div> <ul class="errorlist" id="id_radio_error"><li>'
            'This field is required.</li> </ul> <div id="id_radio"><div><label '
            'for="id_radio_0"><input type="radio" name="radio" value="a" required '
            'aria-invalid="true" id="id_radio_0" />A</label></div><div><label '
            'for="id_radio_1"><input type="radio" name="radio" value="b" required '
            'aria-invalid="true" id="id_radio_1" />B</label></div></div></fieldset>'
            '</div><div><fieldset aria-describedby="id_datetime_helptext '
            'id_datetime_error"><legend>Datetime:</legend><div class="helptext" '
            'id="id_datetime_helptext">Enter Date and Time</div><ul class="errorlist" '
            'id="id_datetime_error"><li>This field is required.</li></ul><input '
            'type="text" name="datetime_0" required aria-invalid="true" '
            'id="id_datetime_0" /><input type="text" name="datetime_1" required '
            'aria-invalid="true" id="id_datetime_1" /></fieldset></div>',
            str(f),
        )
        f = FieldsetForm(auto_id=False)
        # aria-describedby is not included.
        self.assertIn("<fieldset>", str(f))
        self.assertIn('<div class="helptext">', str(f))
        f = FieldsetForm(auto_id="custom_%s")
        # aria-describedby uses custom auto_id.
        self.assertIn('fieldset aria-describedby="custom_checkbox_helptext"', str(f))
        self.assertIn('<div class="helptext" id="custom_checkbox_helptext">', str(f))