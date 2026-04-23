def test_empty_filter_aggregate(self):
        self.assertEqual(
            Author.objects.filter(id__in=[])
            .annotate(Count("friends"))
            .aggregate(Count("pk")),
            {"pk__count": 0},
        )