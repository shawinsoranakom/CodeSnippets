def test_dates(self):
        instance = DateTimeArrayModel(
            datetimes=[timezone.now()],
            dates=[timezone.now().date()],
            times=[timezone.now().time()],
        )
        instance.save()
        loaded = DateTimeArrayModel.objects.get()
        self.assertEqual(instance.datetimes, loaded.datetimes)
        self.assertEqual(instance.dates, loaded.dates)
        self.assertEqual(instance.times, loaded.times)