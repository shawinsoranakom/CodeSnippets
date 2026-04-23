def test_values_queryset_non_conflict(self):
        # If you're using a values query set, some potential conflicts are
        # avoided.
        # age is a field on Author, so it shouldn't be allowed as an aggregate.
        # But age isn't included in values(), so it is.
        results = (
            Author.objects.values("name")
            .annotate(age=Count("book_contact_set"))
            .order_by("name")
        )
        self.assertEqual(len(results), 9)
        self.assertEqual(results[0]["name"], "Adrian Holovaty")
        self.assertEqual(results[0]["age"], 1)

        # Same problem, but aggregating over m2m fields
        results = (
            Author.objects.values("name")
            .annotate(age=Avg("friends__age"))
            .order_by("name")
        )
        self.assertEqual(len(results), 9)
        self.assertEqual(results[0]["name"], "Adrian Holovaty")
        self.assertEqual(results[0]["age"], 32.0)

        # Same problem, but colliding with an m2m field
        results = (
            Author.objects.values("name")
            .annotate(friends=Count("friends"))
            .order_by("name")
        )
        self.assertEqual(len(results), 9)
        self.assertEqual(results[0]["name"], "Adrian Holovaty")
        self.assertEqual(results[0]["friends"], 2)