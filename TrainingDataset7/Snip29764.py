def test_contained_by(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__contained_by={"a": "b", "c": "d"}),
            self.objs[:4],
        )