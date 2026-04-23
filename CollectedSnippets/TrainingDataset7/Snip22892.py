def test_custom_renderer_field_template_name(self):
        class Person(Form):
            first_name = CharField()

        t = Template("{{ form.first_name.as_field_group }}")
        html = t.render(Context({"form": Person()}))
        expected = """
        <label for="id_first_name">First name:</label>
        <p>Custom Field</p>
        <input type="text" name="first_name" required id="id_first_name">
        """
        self.assertHTMLEqual(html, expected)