def test_django_html_escaping(self):
        if self.backend_name == "dummy":
            self.skipTest("test doesn't apply to dummy backend")

        class TestForm(Form):
            test_field = CharField()

        media = Media(js=["my-script.js"])
        form = TestForm()
        template = self.engine.get_template("template_backends/django_escaping.html")
        content = template.render({"media": media, "test_form": form})

        expected = "{}\n\n{}\n\n{}".format(media, form, form["test_field"])

        self.assertHTMLEqual(content, expected)