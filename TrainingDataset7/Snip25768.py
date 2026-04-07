def test_in_bulk_meta_constraint(self):
        season_2011 = Season.objects.create(year=2011)
        season_2012 = Season.objects.create(year=2012)
        Season.objects.create(year=2013)
        self.assertEqual(
            Season.objects.in_bulk(
                [season_2011.year, season_2012.year],
                field_name="year",
            ),
            {season_2011.year: season_2011, season_2012.year: season_2012},
        )