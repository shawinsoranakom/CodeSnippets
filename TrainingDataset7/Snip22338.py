def test_get_flatpages_with_prefix_for_user(self):
        """
        The flatpage template tag retrieve prefixed flatpages for an
        authenticated user.
        """
        me = User.objects.create_user("testuser", "test@example.com", "s3krit")
        out = Template(
            "{% load flatpages %}"
            "{% get_flatpages '/location/' for me as location_flatpages %}"
            "{% for page in location_flatpages %}"
            "{{ page.title }},"
            "{% endfor %}"
        ).render(Context({"me": me}))
        self.assertEqual(out, "A Nested Flatpage,Sekrit Nested Flatpage,")