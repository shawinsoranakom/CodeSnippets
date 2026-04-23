def test_contains(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__contains={"a": "b"}), self.objs[:2]
        )