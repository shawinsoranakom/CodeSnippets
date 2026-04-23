def test_extended_bodyclass_template_index(self):
        """
        The admin/index.html template uses block.super in the bodyclass block.
        """
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "bodyclass_consistency_check ")