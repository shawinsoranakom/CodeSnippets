def test_field_chaining_istartswith(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__cat__istartswith="kit"),
            self.objs[7:],
        )