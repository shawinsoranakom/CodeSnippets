def test_exact_times(self):
        self.assertSequenceEqual(
            DateTimeArrayModel.objects.filter(times=self.times), self.objs
        )