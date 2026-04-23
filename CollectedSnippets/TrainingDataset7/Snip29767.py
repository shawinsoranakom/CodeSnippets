def test_has_key(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__has_key="c"), self.objs[1:3]
        )