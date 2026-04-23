def test_field_chaining_regex(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__cat__regex=r"ou$"),
            [self.objs[6]],
        )