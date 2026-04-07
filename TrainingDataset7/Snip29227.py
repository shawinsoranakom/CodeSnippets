def test_inheritance(self):
        Event.objects.create()
        Screening.objects.create(movie=self.movie)

        self.assertEqual(len(Event.objects.all()), 2)
        self.assertEqual(len(Event.objects.select_related("screening")), 2)
        # This failed.
        self.assertEqual(len(Event.objects.select_related("screening__movie")), 2)

        self.assertEqual(len(Event.objects.values()), 2)
        self.assertEqual(len(Event.objects.values("screening__pk")), 2)
        self.assertEqual(len(Event.objects.values("screening__movie__pk")), 2)
        self.assertEqual(len(Event.objects.values("screening__movie__title")), 2)
        # This failed.
        self.assertEqual(
            len(
                Event.objects.values("screening__movie__pk", "screening__movie__title")
            ),
            2,
        )

        # Simple filter/exclude queries for good measure.
        self.assertEqual(Event.objects.filter(screening__movie=self.movie).count(), 1)
        self.assertEqual(Event.objects.exclude(screening__movie=self.movie).count(), 1)