def test_get_flatpages_tag_for_user(self):
        """
        The flatpage template tag retrieves all flatpages for an authenticated
        user
        """
        me = User.objects.create_user("testuser", "test@example.com", "s3krit")
        out = Template(
            "{% load flatpages %}"
            "{% get_flatpages for me as flatpages %}"
            "{% for page in flatpages %}"
            "{{ page.title }},"
            "{% endfor %}"
        ).render(Context({"me": me}))
        self.assertEqual(
            out, "A Flatpage,A Nested Flatpage,Sekrit Nested Flatpage,Sekrit Flatpage,"
        )