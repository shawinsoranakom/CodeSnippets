def test_basic_ordering(self):
        self.assertIs(Author.objects.all().totally_ordered, True)
        self.assertIs(Author.objects.order_by("name").totally_ordered, False)
        self.assertIs(BarcodedArticle.objects.order_by("rank").totally_ordered, False)
        self.assertIs(
            BarcodedArticle.objects.order_by("rank", "pk").totally_ordered, True
        )