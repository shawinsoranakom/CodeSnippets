def test_parent_fk_available_in_child(self):
        qs = (
            Author.objects.select_related("authorwithage")
            .prefetch_related("first_book")
            .filter(pk=self.child.pk)
        )
        with self.assertNumQueries(2):
            results = list(qs)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].authorwithage.first_book, self.book)