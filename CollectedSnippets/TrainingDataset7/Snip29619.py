def test_exact_dates(self):
        self.assertSequenceEqual(
            DateTimeArrayModel.objects.filter(dates=self.dates), self.objs
        )