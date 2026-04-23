def test_deconstruction(self):
        index = SpGistIndex(fields=["title"], name="test_title_spgist", fillfactor=80)
        path, args, kwargs = index.deconstruct()
        self.assertEqual(path, "django.contrib.postgres.indexes.SpGistIndex")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs, {"fields": ["title"], "name": "test_title_spgist", "fillfactor": 80}
        )