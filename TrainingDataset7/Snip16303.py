def test_change_list_sorting_model_admin_reverse(self):
        """
        Ensure we can sort on a list_display field that is a ModelAdmin
        method in reverse order (i.e. admin_order_field uses the '-' prefix)
        (column 6 is 'model_year_reverse' in ArticleAdmin)
        """
        td = '<td class="field-model_property_year">%s</td>'
        td_2000, td_2008, td_2009 = td % 2000, td % 2008, td % 2009
        response = self.client.get(
            reverse("admin:admin_views_article_changelist"), {"o": "6"}
        )
        self.assertContentBefore(
            response,
            td_2009,
            td_2008,
            "Results of sorting on ModelAdmin method are out of order.",
        )
        self.assertContentBefore(
            response,
            td_2008,
            td_2000,
            "Results of sorting on ModelAdmin method are out of order.",
        )
        # Let's make sure the ordering is right and that we don't get a
        # FieldError when we change to descending order
        response = self.client.get(
            reverse("admin:admin_views_article_changelist"), {"o": "-6"}
        )
        self.assertContentBefore(
            response,
            td_2000,
            td_2008,
            "Results of sorting on ModelAdmin method are out of order.",
        )
        self.assertContentBefore(
            response,
            td_2008,
            td_2009,
            "Results of sorting on ModelAdmin method are out of order.",
        )