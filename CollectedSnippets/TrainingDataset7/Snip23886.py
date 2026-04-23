def test_first_last_empty_order_by_clears_default_ordering(self):
        OrderedArticle.objects.create(
            headline="Article 1",
            pub_date=datetime(2006, 9, 10),
        )

        qs = OrderedArticle.objects.order_by()
        with patch.object(type(qs), "order_by") as mock_order_by:
            qs.first()
            mock_order_by.assert_not_called()
            qs.last()
            mock_order_by.assert_not_called()