def test_more_aggregation(self):
        a = Author.objects.get(name__contains="Norvig")
        b = Book.objects.get(name__contains="Done Right")
        b.authors.add(a)
        b.save()

        vals = (
            Book.objects.annotate(num_authors=Count("authors__id"))
            .filter(authors__name__contains="Norvig", num_authors__gt=1)
            .aggregate(Avg("rating"))
        )
        self.assertEqual(vals, {"rating__avg": 4.25})