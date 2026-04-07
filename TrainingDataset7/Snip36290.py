def test(self):
        deltas = [
            datetime.timedelta.max,
            datetime.timedelta.min,
            datetime.timedelta.resolution,
            -datetime.timedelta.resolution,
            datetime.timedelta(microseconds=8999999999999999),
        ]
        for delta in deltas:
            with self.subTest(delta=delta):
                self.assertEqual(
                    datetime.timedelta(microseconds=duration_microseconds(delta)), delta
                )