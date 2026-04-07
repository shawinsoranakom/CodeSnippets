def test_change_list_sorting_model_admin(self):
        """
        Ensure we can sort on a list_display field that is a ModelAdmin method
        (column 4 is 'modeladmin_year' in ArticleAdmin)
        """
        response = self.client.get(
            reverse("admin:admin_views_article_changelist"), {"o": "4"}
        )
        self.assertContentBefore(
            response,
            "Oldest content",
            "Middle content",
            "Results of sorting on ModelAdmin method are out of order.",
        )
        self.assertContentBefore(
            response,
            "Middle content",
            "Newest content",
            "Results of sorting on ModelAdmin method are out of order.",
        )