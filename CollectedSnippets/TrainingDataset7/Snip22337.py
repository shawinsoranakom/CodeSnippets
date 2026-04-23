def test_get_flatpages_with_prefix_for_anon_user(self):
        """
        The flatpage template tag retrieves unregistered prefixed flatpages for
        an anonymous user.
        """
        out = Template(
            "{% load flatpages %}"
            "{% get_flatpages '/location/' for anonuser as location_flatpages %}"
            "{% for page in location_flatpages %}"
            "{{ page.title }},"
            "{% endfor %}"
        ).render(Context({"anonuser": AnonymousUser()}))
        self.assertEqual(out, "A Nested Flatpage,")