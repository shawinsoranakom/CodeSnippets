def test_datetime_range(self):
        objs = [
            RangeLookupsModel.objects.create(timestamp="2015-01-01T09:00:00"),
            RangeLookupsModel.objects.create(timestamp="2015-05-05T17:00:00"),
        ]
        self.assertSequenceEqual(
            RangeLookupsModel.objects.filter(
                timestamp__contained_by=DateTimeTZRange(
                    "2015-01-01T09:00", "2015-05-04T23:55"
                )
            ),
            [objs[0]],
        )