def test_values(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__values=["b"]), self.objs[:1]
        )