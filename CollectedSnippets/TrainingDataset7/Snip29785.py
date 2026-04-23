def test_keys_contains(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__keys__contains=["a"]), self.objs[:2]
        )