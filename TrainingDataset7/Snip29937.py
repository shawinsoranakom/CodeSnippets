def test_date_range(self):
        objs = [
            RangeLookupsModel.objects.create(date="2015-01-01"),
            RangeLookupsModel.objects.create(date="2015-05-05"),
        ]
        self.assertSequenceEqual(
            RangeLookupsModel.objects.filter(
                date__contained_by=DateRange("2015-01-01", "2015-05-04")
            ),
            [objs[0]],
        )