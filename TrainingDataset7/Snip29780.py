def test_field_chaining_iendswith(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__cat__iendswith="ou"),
            self.objs[5:7],
        )