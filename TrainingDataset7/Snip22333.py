def test_get_flatpages_tag(self):
        """
        The flatpage template tag retrieves unregistered prefixed flatpages by
        default
        """
        out = Template(
            "{% load flatpages %}"
            "{% get_flatpages as flatpages %}"
            "{% for page in flatpages %}"
            "{{ page.title }},"
            "{% endfor %}"
        ).render(Context())
        self.assertEqual(out, "A Flatpage,A Nested Flatpage,")