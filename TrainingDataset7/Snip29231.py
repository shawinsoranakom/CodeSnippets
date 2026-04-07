def test_explicit_ForeignKey_NullFK(self):
        PackageNullFK.objects.create()
        screening = ScreeningNullFK.objects.create(movie=None)
        screening_with_movie = ScreeningNullFK.objects.create(movie=self.movie)
        PackageNullFK.objects.create(screening=screening)
        PackageNullFK.objects.create(screening=screening_with_movie)

        self.assertEqual(len(PackageNullFK.objects.all()), 3)
        self.assertEqual(len(PackageNullFK.objects.select_related("screening")), 3)
        self.assertEqual(
            len(PackageNullFK.objects.select_related("screening__movie")), 3
        )

        self.assertEqual(len(PackageNullFK.objects.values()), 3)
        self.assertEqual(len(PackageNullFK.objects.values("screening__pk")), 3)
        self.assertEqual(len(PackageNullFK.objects.values("screening__movie__pk")), 3)
        self.assertEqual(
            len(PackageNullFK.objects.values("screening__movie__title")), 3
        )
        self.assertEqual(
            len(
                PackageNullFK.objects.values(
                    "screening__movie__pk", "screening__movie__title"
                )
            ),
            3,
        )

        self.assertEqual(
            PackageNullFK.objects.filter(screening__movie=self.movie).count(), 1
        )
        self.assertEqual(
            PackageNullFK.objects.exclude(screening__movie=self.movie).count(), 2
        )