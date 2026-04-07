def test_field_chaining_contains(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__a__contains="b"), self.objs[:2]
        )