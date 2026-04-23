def test_range_object_boundaries_range_with_default_bounds(self):
        range_ = DateTimeTZRange(
            timezone.now(),
            timezone.now() + datetime.timedelta(hours=1),
            bounds="()",
        )
        RangesModel.objects.create(timestamps_closed_bounds=range_)
        loaded = RangesModel.objects.get()
        self.assertEqual(loaded.timestamps_closed_bounds, range_)