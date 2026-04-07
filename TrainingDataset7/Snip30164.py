def test_get(self):
        """
        Objects retrieved with .get() get the prefetch behavior.
        """
        # Need a double
        with self.assertNumQueries(3):
            author = Author.objects.prefetch_related("books__read_by").get(
                name="Charlotte"
            )
            lists = [[str(r) for r in b.read_by.all()] for b in author.books.all()]
            self.assertEqual(lists, [["Amy"], ["Belinda"]])