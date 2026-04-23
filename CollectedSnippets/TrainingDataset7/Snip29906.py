def test_all_fields(self):
        now = timezone.now()
        instance = RangesModel(
            ints=NumericRange(0, 10),
            bigints=NumericRange(10, 20),
            decimals=NumericRange(20, 30),
            timestamps=DateTimeTZRange(now - datetime.timedelta(hours=1), now),
            dates=DateRange(now.date() - datetime.timedelta(days=1), now.date()),
        )
        instance.save()
        loaded = RangesModel.objects.get()
        self.assertEqual(instance.ints, loaded.ints)
        self.assertEqual(instance.bigints, loaded.bigints)
        self.assertEqual(instance.decimals, loaded.decimals)
        self.assertEqual(instance.timestamps, loaded.timestamps)
        self.assertEqual(instance.dates, loaded.dates)