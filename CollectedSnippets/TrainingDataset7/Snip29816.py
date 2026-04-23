def test_deconstruction_no_customization(self):
        index = self.index_class(
            fields=["title"], name="test_title_%s" % self.index_class.suffix
        )
        path, args, kwargs = index.deconstruct()
        self.assertEqual(
            path, "django.contrib.postgres.indexes.%s" % self.index_class.__name__
        )
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs,
            {"fields": ["title"], "name": "test_title_%s" % self.index_class.suffix},
        )