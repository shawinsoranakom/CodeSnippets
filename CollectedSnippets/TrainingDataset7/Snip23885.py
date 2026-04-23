def test_first_last_empty_order_by_has_no_pk_ordering(self):
        Article.objects.create(
            headline="Article 1",
            pub_date=datetime(2006, 9, 10),
            expire_date=datetime(2056, 9, 11),
        )

        qs = Article.objects.order_by()
        with patch.object(type(qs), "order_by") as mock_order_by:
            qs.first()
            mock_order_by.assert_not_called()
            qs.last()
            mock_order_by.assert_not_called()