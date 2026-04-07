def test_obj_subquery_lookup(self):
        qs = NullableJSONModel.objects.annotate(
            field=Subquery(
                NullableJSONModel.objects.filter(pk=OuterRef("pk")).values("value")
            ),
        ).filter(field__a="b")
        self.assertCountEqual(qs, [self.objs[3], self.objs[4]])