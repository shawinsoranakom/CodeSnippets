def test_legend_tag(self):
        class CustomFrameworkForm(FrameworkForm):
            template_name = "forms_tests/legend_test.html"
            required_css_class = "required"

        f = CustomFrameworkForm()
        self.assertHTMLEqual(
            str(f),
            '<label for="id_name" class="required">Name:</label>'
            '<legend class="required">Language:</legend>',
        )