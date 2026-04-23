def test_plain_annotate(self):
        agg = Sum("book__pages", filter=Q(book__rating__gt=3))
        qs = Author.objects.annotate(pages=agg).order_by("pk")
        self.assertSequenceEqual([a.pages for a in qs], [447, None, 1047])