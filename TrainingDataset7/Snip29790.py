def test_obj_subquery_lookup(self):
        qs = HStoreModel.objects.annotate(
            value=Subquery(
                HStoreModel.objects.filter(pk=OuterRef("pk")).values("field")
            ),
        ).filter(value__a="b")
        self.assertSequenceEqual(qs, self.objs[:2])