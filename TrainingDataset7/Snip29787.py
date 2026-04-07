def test_key_isnull(self):
        obj = HStoreModel.objects.create(field={"a": None})
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__a__isnull=True),
            self.objs[2:9] + [obj],
        )
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__a__isnull=False), self.objs[:2]
        )