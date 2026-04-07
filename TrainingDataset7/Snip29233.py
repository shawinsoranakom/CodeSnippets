def test_inheritance(self):
        Event.objects.create()
        Screening.objects.create(movie=self.movie)

        self.assertEqual(len(Event.objects.all()), 2)
        self.assertEqual(
            len(Event.objects.select_related("screening__movie__director")), 2
        )

        self.assertEqual(len(Event.objects.values()), 2)
        self.assertEqual(len(Event.objects.values("screening__movie__director__pk")), 2)
        self.assertEqual(
            len(Event.objects.values("screening__movie__director__name")), 2
        )
        self.assertEqual(
            len(
                Event.objects.values(
                    "screening__movie__director__pk", "screening__movie__director__name"
                )
            ),
            2,
        )
        self.assertEqual(
            len(
                Event.objects.values(
                    "screening__movie__pk", "screening__movie__director__pk"
                )
            ),
            2,
        )
        self.assertEqual(
            len(
                Event.objects.values(
                    "screening__movie__pk", "screening__movie__director__name"
                )
            ),
            2,
        )
        self.assertEqual(
            len(
                Event.objects.values(
                    "screening__movie__title", "screening__movie__director__pk"
                )
            ),
            2,
        )
        self.assertEqual(
            len(
                Event.objects.values(
                    "screening__movie__title", "screening__movie__director__name"
                )
            ),
            2,
        )

        self.assertEqual(
            Event.objects.filter(screening__movie__director=self.director).count(), 1
        )
        self.assertEqual(
            Event.objects.exclude(screening__movie__director=self.director).count(), 1
        )