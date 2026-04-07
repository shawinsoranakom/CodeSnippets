def test_custom_field_render_template(self):
        class MyForm(Form):
            first_name = CharField()

        f = MyForm()
        self.assertHTMLEqual(
            f["first_name"].render(template_name="forms_tests/custom_field.html"),
            '<label for="id_first_name">First name:</label><p>Custom Field</p>'
            '<input type="text" name="first_name" required id="id_first_name">',
        )