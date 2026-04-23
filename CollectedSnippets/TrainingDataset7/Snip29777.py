def test_field_chaining_startswith(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__cat__startswith="kit"),
            [self.objs[7]],
        )