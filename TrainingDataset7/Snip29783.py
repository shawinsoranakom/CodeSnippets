def test_field_chaining_iregex(self):
        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__cat__iregex=r"oU$"),
            self.objs[5:7],
        )