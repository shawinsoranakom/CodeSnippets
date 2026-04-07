def test_extended_bodyclass_template_change_form(self):
        """
        The admin/change_form.html template uses block.super in the
        bodyclass block.
        """
        response = self.client.get(reverse("admin:admin_views_section_add"))
        self.assertContains(response, "bodyclass_consistency_check ")