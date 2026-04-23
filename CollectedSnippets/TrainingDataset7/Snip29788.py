def test_usage_in_subquery(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(id__in=HStoreModel.objects.filter(field__a="b")),
            self.objs[:2],
        )