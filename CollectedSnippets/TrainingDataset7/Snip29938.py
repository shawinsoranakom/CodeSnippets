def test_date_range_datetime_field(self):
        objs = [
            RangeLookupsModel.objects.create(timestamp="2015-01-01"),
            RangeLookupsModel.objects.create(timestamp="2015-05-05"),
        ]
        self.assertSequenceEqual(
            RangeLookupsModel.objects.filter(
                timestamp__date__contained_by=DateRange("2015-01-01", "2015-05-04")
            ),
            [objs[0]],
        )