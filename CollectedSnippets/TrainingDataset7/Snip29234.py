def test_explicit_ForeignKey(self):
        Package.objects.create()
        screening = Screening.objects.create(movie=self.movie)
        Package.objects.create(screening=screening)

        self.assertEqual(len(Package.objects.all()), 2)
        self.assertEqual(
            len(Package.objects.select_related("screening__movie__director")), 2
        )

        self.assertEqual(len(Package.objects.values()), 2)
        self.assertEqual(
            len(Package.objects.values("screening__movie__director__pk")), 2
        )
        self.assertEqual(
            len(Package.objects.values("screening__movie__director__name")), 2
        )
        self.assertEqual(
            len(
                Package.objects.values(
                    "screening__movie__director__pk", "screening__movie__director__name"
                )
            ),
            2,
        )
        self.assertEqual(
            len(
                Package.objects.values(
                    "screening__movie__pk", "screening__movie__director__pk"
                )
            ),
            2,
        )
        self.assertEqual(
            len(
                Package.objects.values(
                    "screening__movie__pk", "screening__movie__director__name"
                )
            ),
            2,
        )
        self.assertEqual(
            len(
                Package.objects.values(
                    "screening__movie__title", "screening__movie__director__pk"
                )
            ),
            2,
        )
        self.assertEqual(
            len(
                Package.objects.values(
                    "screening__movie__title", "screening__movie__director__name"
                )
            ),
            2,
        )

        self.assertEqual(
            Package.objects.filter(screening__movie__director=self.director).count(), 1
        )
        self.assertEqual(
            Package.objects.exclude(screening__movie__director=self.director).count(), 1
        )