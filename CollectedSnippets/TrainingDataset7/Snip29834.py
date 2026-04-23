def test_deconstruction(self):
        index = HashIndex(fields=["title"], name="test_title_hash", fillfactor=80)
        path, args, kwargs = index.deconstruct()
        self.assertEqual(path, "django.contrib.postgres.indexes.HashIndex")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs, {"fields": ["title"], "name": "test_title_hash", "fillfactor": 80}
        )