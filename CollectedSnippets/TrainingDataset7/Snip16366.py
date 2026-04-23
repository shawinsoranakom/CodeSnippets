def test_extended_bodyclass_change_list(self):
        """
        The admin/change_list.html' template uses block.super
        in the bodyclass block.
        """
        response = self.client.get(reverse("admin:admin_views_article_changelist"))
        self.assertContains(response, "bodyclass_consistency_check ")