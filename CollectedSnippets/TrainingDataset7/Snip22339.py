def test_get_flatpages_with_variable_prefix(self):
        "The prefix for the flatpage template tag can be a template variable"
        out = Template(
            "{% load flatpages %}"
            "{% get_flatpages location_prefix as location_flatpages %}"
            "{% for page in location_flatpages %}"
            "{{ page.title }},"
            "{% endfor %}"
        ).render(Context({"location_prefix": "/location/"}))
        self.assertEqual(out, "A Nested Flatpage,")