def test_order_by_field(self):
        more_objs = (
            HStoreModel.objects.create(field={"g": "637"}),
            HStoreModel.objects.create(field={"g": "002"}),
            HStoreModel.objects.create(field={"g": "042"}),
            HStoreModel.objects.create(field={"g": "981"}),
        )
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__has_key="g").order_by("field__g"),
            [more_objs[1], more_objs[2], more_objs[0], more_objs[3]],
        )