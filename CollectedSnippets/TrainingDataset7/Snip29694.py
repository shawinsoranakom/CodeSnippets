def test_bulk_create(self):
        OffByOneModel.objects.bulk_create(OffByOneModel(one_off=0) for _ in range(20))

        self.assertSequenceEqual(
            [m.one_off for m in OffByOneModel.objects.all()], 20 * [1]
        )