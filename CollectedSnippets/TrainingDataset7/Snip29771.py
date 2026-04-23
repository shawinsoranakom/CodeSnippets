def test_key_transform_raw_expression(self):
        expr = RawSQL("%s::hstore", ["x => b, y => c"])
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__a=KeyTransform("x", expr)), self.objs[:2]
        )