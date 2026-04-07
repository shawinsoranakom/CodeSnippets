def test_custom_renderer_template_name(self):
        class Person(Form):
            first_name = CharField()

        t = Template("{{ form }}")
        html = t.render(Context({"form": Person()}))
        expected = """
        <div class="fieldWrapper"><label for="id_first_name">First name:</label>
        <input type="text" name="first_name" required id="id_first_name"></div>
        """
        self.assertHTMLEqual(html, expected)