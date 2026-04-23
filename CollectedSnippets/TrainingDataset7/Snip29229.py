def test_null_exclude(self):
        screening = ScreeningNullFK.objects.create(movie=None)
        ScreeningNullFK.objects.create(movie=self.movie)
        self.assertEqual(
            list(ScreeningNullFK.objects.exclude(movie__id=self.movie.pk)), [screening]
        )