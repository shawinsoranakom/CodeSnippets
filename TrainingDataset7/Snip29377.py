def test_conditional_constraints(self):
        self.assertIs(BarcodedArticle.objects.order_by("rank").totally_ordered, False)
        self.assertIs(BarcodedArticle.objects.order_by("barcode").totally_ordered, True)