def test_has_any_keys(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__has_any_keys=["a", "c"]), self.objs[:3]
        )