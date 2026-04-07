def test_add_with_GET_args(self):
        response = self.client.get(
            reverse("admin:admin_views_section_add"), {"name": "My Section"}
        )
        self.assertContains(
            response,
            'value="My Section"',
            msg_prefix="Couldn't find an input with the right value in the response",
        )