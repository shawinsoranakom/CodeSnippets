def test_key_transform_annotation(self):
        qs = HStoreModel.objects.annotate(a=F("field__a"))
        self.assertCountEqual(
            qs.values_list("a", flat=True),
            ["b", "b", None, None, None, None, None, None, None],
        )