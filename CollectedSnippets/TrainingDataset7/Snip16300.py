def test_change_list_sorting_callable_query_expression_reverse(self):
        tests = [
            ("order_by_expression", -9),
            ("order_by_f_expression", -12),
            ("order_by_orderby_expression", -13),
        ]
        for admin_order_field, index in tests:
            with self.subTest(admin_order_field):
                response = self.client.get(
                    reverse("admin:admin_views_article_changelist"),
                    {"o": index},
                )
                self.assertContentBefore(
                    response,
                    "Middle content",
                    "Oldest content",
                    "Results of sorting on callable are out of order.",
                )
                self.assertContentBefore(
                    response,
                    "Newest content",
                    "Middle content",
                    "Results of sorting on callable are out of order.",
                )