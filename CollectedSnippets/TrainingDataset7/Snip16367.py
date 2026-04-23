def test_extended_bodyclass_template_login(self):
        """
        The admin/login.html template uses block.super in the
        bodyclass block.
        """
        self.client.logout()
        response = self.client.get(reverse("admin:login"))
        self.assertContains(response, "bodyclass_consistency_check ")