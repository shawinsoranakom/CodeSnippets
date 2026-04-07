def test_deconstruction(self):
        index = GistIndex(
            fields=["title"], name="test_title_gist", buffering=False, fillfactor=80
        )
        path, args, kwargs = index.deconstruct()
        self.assertEqual(path, "django.contrib.postgres.indexes.GistIndex")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs,
            {
                "fields": ["title"],
                "name": "test_title_gist",
                "buffering": False,
                "fillfactor": 80,
            },
        )