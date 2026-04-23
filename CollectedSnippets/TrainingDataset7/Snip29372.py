def test_composite_constraints(self):
        qs = BarcodedArticle.objects.order_by("pub_date", "rank")
        self.assertIs(qs.totally_ordered, False)
        qs = BarcodedArticle.objects.order_by("headline", "slug")
        self.assertIs(qs.totally_ordered, True)