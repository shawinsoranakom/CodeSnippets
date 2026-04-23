def test_field_chaining_iexact(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__breed__iexact="persian"),
            self.objs[7:],
        )