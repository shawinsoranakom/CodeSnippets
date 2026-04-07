def test_in_bulk_multiple_distinct_field(self):
        msg = "in_bulk()'s field_name must be a unique field but 'pub_date' isn't."
        with self.assertRaisesMessage(ValueError, msg):
            Article.objects.order_by("headline", "pub_date").distinct(
                "headline",
                "pub_date",
            ).in_bulk(field_name="pub_date")