def test_group_by_nested_expression_with_params(self):
        greatest_pages_param = "greatest_pages"
        if connection.vendor == "mysql" and connection.features.supports_any_value:
            greatest_pages_param = AnyValue("greatest_pages")

        books_qs = (
            Book.objects.annotate(greatest_pages=Greatest("pages", Value(600)))
            .values(
                "greatest_pages",
            )
            .annotate(
                min_pages=Min("pages"),
                least=Least("min_pages", greatest_pages_param),
            )
            .values_list("least", flat=True)
        )
        self.assertCountEqual(books_qs, [300, 946, 1132])