def test_key_transform(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__a="b"), self.objs[:2]
        )