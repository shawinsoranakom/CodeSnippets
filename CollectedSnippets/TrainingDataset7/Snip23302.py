def test_fieldset(self):
        class TestForm(Form):
            template_name = "forms_tests/use_fieldset.html"
            field = ComplexField(widget=ComplexMultiWidget)

        form = TestForm()
        self.assertIs(form["field"].field.widget.use_fieldset, True)
        self.assertHTMLEqual(
            "<div><fieldset><legend>Field:</legend>"
            '<input type="text" name="field_0" required id="id_field_0">'
            '<select name="field_1" required id="id_field_1" multiple>'
            '<option value="J">John</option><option value="P">Paul</option>'
            '<option value="G">George</option><option value="R">Ringo</option></select>'
            '<input type="text" name="field_2_0" required id="id_field_2_0">'
            '<input type="text" name="field_2_1" required id="id_field_2_1">'
            "</fieldset></div>",
            form.render(),
        )