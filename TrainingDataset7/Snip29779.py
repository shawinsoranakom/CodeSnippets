def test_field_chaining_endswith(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__cat__endswith="ou"),
            [self.objs[6]],
        )