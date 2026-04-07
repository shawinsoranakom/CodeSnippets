def test_explicit_ForeignKey(self):
        Package.objects.create()
        screening = Screening.objects.create(movie=self.movie)
        Package.objects.create(screening=screening)

        self.assertEqual(len(Package.objects.all()), 2)
        self.assertEqual(len(Package.objects.select_related("screening")), 2)
        self.assertEqual(len(Package.objects.select_related("screening__movie")), 2)

        self.assertEqual(len(Package.objects.values()), 2)
        self.assertEqual(len(Package.objects.values("screening__pk")), 2)
        self.assertEqual(len(Package.objects.values("screening__movie__pk")), 2)
        self.assertEqual(len(Package.objects.values("screening__movie__title")), 2)
        # This failed.
        self.assertEqual(
            len(
                Package.objects.values(
                    "screening__movie__pk", "screening__movie__title"
                )
            ),
            2,
        )

        self.assertEqual(Package.objects.filter(screening__movie=self.movie).count(), 1)
        self.assertEqual(
            Package.objects.exclude(screening__movie=self.movie).count(), 1
        )