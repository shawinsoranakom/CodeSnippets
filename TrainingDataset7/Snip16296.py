def test_change_list_sorting_callable(self):
        """
        Ensure we can sort on a list_display field that is a callable
        (column 2 is callable_year in ArticleAdmin)
        """
        response = self.client.get(
            reverse("admin:admin_views_article_changelist"), {"o": 2}
        )
        self.assertContentBefore(
            response,
            "Oldest content",
            "Middle content",
            "Results of sorting on callable are out of order.",
        )
        self.assertContentBefore(
            response,
            "Middle content",
            "Newest content",
            "Results of sorting on callable are out of order.",
        )