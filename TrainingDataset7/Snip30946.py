def test_annotation_values_list(self):
        # values_list() is reloaded to values() when using a pickled query.
        tests = [
            Happening.objects.values_list("name"),
            Happening.objects.values_list("name", flat=True),
            Happening.objects.values_list("name", named=True),
        ]
        for qs in tests:
            with self.subTest(qs._iterable_class.__name__):
                reloaded = Happening.objects.all()
                reloaded.query = pickle.loads(pickle.dumps(qs.query))
                self.assertEqual(reloaded.get(), {"name": "test"})