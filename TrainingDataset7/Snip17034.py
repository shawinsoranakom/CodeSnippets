def test_exists_none_with_aggregate(self):
        qs = Book.objects.annotate(
            count=Count("id"),
            exists=Exists(Author.objects.none()),
        )
        self.assertEqual(len(qs), 6)