def test_has_keys(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__has_keys=["a", "c"]), self.objs[1:2]
        )