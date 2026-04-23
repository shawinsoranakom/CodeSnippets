def test_inheritance_null_FK(self):
        Event.objects.create()
        ScreeningNullFK.objects.create(movie=None)
        ScreeningNullFK.objects.create(movie=self.movie)

        self.assertEqual(len(Event.objects.all()), 3)
        self.assertEqual(len(Event.objects.select_related("screeningnullfk")), 3)
        self.assertEqual(len(Event.objects.select_related("screeningnullfk__movie")), 3)

        self.assertEqual(len(Event.objects.values()), 3)
        self.assertEqual(len(Event.objects.values("screeningnullfk__pk")), 3)
        self.assertEqual(len(Event.objects.values("screeningnullfk__movie__pk")), 3)
        self.assertEqual(len(Event.objects.values("screeningnullfk__movie__title")), 3)
        self.assertEqual(
            len(
                Event.objects.values(
                    "screeningnullfk__movie__pk", "screeningnullfk__movie__title"
                )
            ),
            3,
        )

        self.assertEqual(
            Event.objects.filter(screeningnullfk__movie=self.movie).count(), 1
        )
        self.assertEqual(
            Event.objects.exclude(screeningnullfk__movie=self.movie).count(), 2
        )