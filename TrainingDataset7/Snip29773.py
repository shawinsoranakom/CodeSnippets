def test_keys(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__keys=["a"]), self.objs[:1]
        )