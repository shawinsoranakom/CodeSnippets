def test_auto_field_contained_by(self):
        objs = RangeLookupsModel.objects.bulk_create(
            [RangeLookupsModel() for i in range(1, 5)]
        )
        self.assertSequenceEqual(
            RangeLookupsModel.objects.filter(
                id__contained_by=NumericRange(objs[1].pk, objs[3].pk),
            ),
            objs[1:3],
        )