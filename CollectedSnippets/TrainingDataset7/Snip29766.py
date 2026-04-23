def test_in_generator(self):
        def search():
            yield {"a": "b"}

        self.assertSequenceEqual(
            HStoreModel.objects.filter(field__in=search()), self.objs[:1]
        )