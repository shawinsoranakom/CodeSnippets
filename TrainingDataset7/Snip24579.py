def test12b_count(self):
        "Testing `Count` aggregate on non geo-fields."
        # Should only be one author (Trevor Paglen) returned by this query, and
        # the annotation should have 3 for the number of books, see #11087.
        # Also testing with a values(), see #11489.
        qs = Author.objects.annotate(num_books=Count("books")).filter(num_books__gt=1)
        vqs = (
            Author.objects.values("name")
            .annotate(num_books=Count("books"))
            .filter(num_books__gt=1)
        )
        self.assertEqual(1, len(qs))
        self.assertEqual(3, qs[0].num_books)
        self.assertEqual(1, len(vqs))
        self.assertEqual(3, vqs[0]["num_books"])