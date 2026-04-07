def test_order_by_constant_value(self):
        # Order by annotated constant from selected columns.
        qs = Article.objects.annotate(
            constant=Value("1", output_field=CharField()),
        ).order_by("constant", "-headline")
        self.assertSequenceEqual(qs, [self.a4, self.a3, self.a2, self.a1])
        # Order by annotated constant which is out of selected columns.
        self.assertSequenceEqual(
            qs.values_list("headline", flat=True),
            [
                "Article 4",
                "Article 3",
                "Article 2",
                "Article 1",
            ],
        )
        # Order by constant.
        qs = Article.objects.order_by(Value("1", output_field=CharField()), "-headline")
        self.assertSequenceEqual(qs, [self.a4, self.a3, self.a2, self.a1])