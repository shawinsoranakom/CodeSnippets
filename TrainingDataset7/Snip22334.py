def test_get_flatpages_tag_for_anon_user(self):
        """
        The flatpage template tag retrieves unregistered flatpages for an
        anonymous user.
        """
        out = Template(
            "{% load flatpages %}"
            "{% get_flatpages for anonuser as flatpages %}"
            "{% for page in flatpages %}"
            "{{ page.title }},"
            "{% endfor %}"
        ).render(Context({"anonuser": AnonymousUser()}))
        self.assertEqual(out, "A Flatpage,A Nested Flatpage,")