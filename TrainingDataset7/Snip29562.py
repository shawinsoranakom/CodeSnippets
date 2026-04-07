def test_bulk_create_with_sized_arrayfield(self):
        objs = WithSizeArrayModel.objects.bulk_create(
            [
                WithSizeArrayModel(field=[1, 2]),
                WithSizeArrayModel(field=[3, 4]),
            ]
        )
        self.assertEqual(objs[0].field, [1, 2])
        self.assertEqual(objs[1].field, [3, 4])