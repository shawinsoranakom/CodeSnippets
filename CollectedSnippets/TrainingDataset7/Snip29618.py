def test_exact_datetimes(self):
        self.assertSequenceEqual(
            DateTimeArrayModel.objects.filter(datetimes=self.datetimes), self.objs
        )