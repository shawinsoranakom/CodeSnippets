def test_order_by_expr_query_reuse(self):
        qs = Author.objects.annotate(num=Count("article")).order_by(
            F("num").desc(), "pk"
        )
        self.assertCountEqual(qs, qs.iterator())