def test_big_auto_field_contained_by(self):
        objs = BigAutoFieldModel.objects.bulk_create(
            [BigAutoFieldModel() for i in range(1, 5)]
        )
        self.assertSequenceEqual(
            BigAutoFieldModel.objects.filter(
                id__contained_by=NumericRange(objs[1].pk, objs[3].pk),
            ),
            objs[1:3],
        )