def test_custom_field_template(self):
        class MyForm(Form):
            first_name = CharField(template_name="forms_tests/custom_field.html")

        f = MyForm()
        self.assertHTMLEqual(
            f.render(),
            '<div><label for="id_first_name">First name:</label><p>Custom Field</p>'
            '<input type="text" name="first_name" required id="id_first_name"></div>',
        )