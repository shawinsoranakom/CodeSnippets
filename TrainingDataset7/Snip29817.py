def test_deconstruction_with_expressions_no_customization(self):
        name = f"test_title_{self.index_class.suffix}"
        index = self.index_class(Lower("title"), name=name)
        path, args, kwargs = index.deconstruct()
        self.assertEqual(
            path,
            f"django.contrib.postgres.indexes.{self.index_class.__name__}",
        )
        self.assertEqual(args, (Lower("title"),))
        self.assertEqual(kwargs, {"name": name})