def test_tuple_range_with_default_bounds(self):
        range_ = (timezone.now(), timezone.now() + datetime.timedelta(hours=1))
        RangesModel.objects.create(timestamps_closed_bounds=range_, timestamps=range_)
        loaded = RangesModel.objects.get()
        self.assertEqual(
            loaded.timestamps_closed_bounds,
            DateTimeTZRange(range_[0], range_[1], "[]"),
        )
        self.assertEqual(
            loaded.timestamps,
            DateTimeTZRange(range_[0], range_[1], "[)"),
        )