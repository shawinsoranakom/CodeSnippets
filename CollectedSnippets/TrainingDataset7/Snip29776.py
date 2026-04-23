def test_field_chaining_icontains(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__cat__icontains="INo"),
            [self.objs[6]],
        )