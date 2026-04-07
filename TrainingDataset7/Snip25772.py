def test_in_bulk_distinct_field(self):
        self.assertEqual(
            Article.objects.order_by("headline")
            .distinct("headline")
            .in_bulk(
                [self.a1.headline, self.a5.headline],
                field_name="headline",
            ),
            {self.a1.headline: self.a1, self.a5.headline: self.a5},
        )