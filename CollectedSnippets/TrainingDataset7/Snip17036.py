def test_exists_extra_where_with_aggregate(self):
        qs = Book.objects.annotate(
            count=Count("id"),
            exists=Exists(Author.objects.extra(where=["1=0"])),
        )
        self.assertEqual(len(qs), 6)