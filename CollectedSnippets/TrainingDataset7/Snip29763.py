def test_exact(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__exact={"a": "b"}), self.objs[:1]
        )