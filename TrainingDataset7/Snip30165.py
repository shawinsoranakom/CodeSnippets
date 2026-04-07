def test_foreign_key_then_m2m(self):
        """
        A m2m relation can be followed after a relation like ForeignKey that
        doesn't have many objects.
        """
        with self.assertNumQueries(2):
            qs = Author.objects.select_related("first_book").prefetch_related(
                "first_book__read_by"
            )
            lists = [[str(r) for r in a.first_book.read_by.all()] for a in qs]
            self.assertEqual(lists, [["Amy"], ["Amy"], ["Amy"], ["Amy", "Belinda"]])