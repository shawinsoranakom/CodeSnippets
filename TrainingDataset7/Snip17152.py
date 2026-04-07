def test_having_subquery_select(self):
        authors = Author.objects.filter(pk=self.a1.pk)
        books = Book.objects.annotate(Count("authors")).filter(
            Q(authors__in=authors) | Q(authors__count__gt=2)
        )
        self.assertEqual(set(books), {self.b1, self.b4})