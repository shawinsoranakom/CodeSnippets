def test_values_overlap(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__values__overlap=["b", "d"]), self.objs[:3]
        )