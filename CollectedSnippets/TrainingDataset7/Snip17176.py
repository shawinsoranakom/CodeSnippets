def test_empty_queryset_annotation(self):
        qs = Author.objects.annotate(empty=Subquery(Author.objects.values("id").none()))
        self.assertIsNone(qs.first().empty)