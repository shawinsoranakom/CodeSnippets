def test_change_list_sorting_property(self):
        """
        Sort on a list_display field that is a property (column 10 is
        a property in Article model).
        """
        response = self.client.get(
            reverse("admin:admin_views_article_changelist"), {"o": 10}
        )
        self.assertContentBefore(
            response,
            "Oldest content",
            "Middle content",
            "Results of sorting on property are out of order.",
        )
        self.assertContentBefore(
            response,
            "Middle content",
            "Newest content",
            "Results of sorting on property are out of order.",
        )