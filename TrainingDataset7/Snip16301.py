def test_change_list_sorting_model(self):
        """
        Ensure we can sort on a list_display field that is a Model method
        (column 3 is 'model_year' in ArticleAdmin)
        """
        response = self.client.get(
            reverse("admin:admin_views_article_changelist"), {"o": "-3"}
        )
        self.assertContentBefore(
            response,
            "Newest content",
            "Middle content",
            "Results of sorting on Model method are out of order.",
        )
        self.assertContentBefore(
            response,
            "Middle content",
            "Oldest content",
            "Results of sorting on Model method are out of order.",
        )