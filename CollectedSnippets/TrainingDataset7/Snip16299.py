def test_change_list_sorting_callable_query_expression(self):
        """Query expressions may be used for admin_order_field."""
        tests = [
            ("order_by_expression", 9),
            ("order_by_f_expression", 12),
            ("order_by_orderby_expression", 13),
        ]
        for admin_order_field, index in tests:
            with self.subTest(admin_order_field):
                response = self.client.get(
                    reverse("admin:admin_views_article_changelist"),
                    {"o": index},
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