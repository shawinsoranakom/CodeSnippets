def test_ordering_select_related_collision(self):
        self.assertEqual(
            Article.objects.select_related("author")
            .annotate(name=Upper("author__name"))
            .filter(pk=self.a1.pk)
            .order_by(OrderBy(F("name")))
            .first(),
            self.a1,
        )
        self.assertEqual(
            Article.objects.select_related("author")
            .annotate(name=Upper("author__name"))
            .filter(pk=self.a1.pk)
            .order_by("name")
            .first(),
            self.a1,
        )