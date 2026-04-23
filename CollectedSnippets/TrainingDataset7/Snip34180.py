def test_repr(self):
        template = Template(
            "<html><body>\n"
            "{% if test %}<h1>{{ varvalue }}</h1>{% endif %}"
            "</body></html>"
        )
        self.assertEqual(
            repr(template),
            '<Template template_string="<html><body>{% if t...">',
        )