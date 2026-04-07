def test_get_flatpages_with_prefix(self):
        """
        The flatpage template tag retrieves unregistered prefixed flatpages by
        default
        """
        out = Template(
            "{% load flatpages %}"
            "{% get_flatpages '/location/' as location_flatpages %}"
            "{% for page in location_flatpages %}"
            "{{ page.title }},"
            "{% endfor %}"
        ).render(Context())
        self.assertEqual(out, "A Nested Flatpage,")