def test_deconstruction(self):
        index = BrinIndex(
            fields=["title"],
            name="test_title_brin",
            autosummarize=True,
            pages_per_range=16,
        )
        path, args, kwargs = index.deconstruct()
        self.assertEqual(path, "django.contrib.postgres.indexes.BrinIndex")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs,
            {
                "fields": ["title"],
                "name": "test_title_brin",
                "autosummarize": True,
                "pages_per_range": 16,
            },
        )