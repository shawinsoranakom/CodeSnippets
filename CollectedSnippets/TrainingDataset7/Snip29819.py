def test_deconstruction(self):
        index = BloomIndex(fields=["title"], name="test_bloom", length=80, columns=[4])
        path, args, kwargs = index.deconstruct()
        self.assertEqual(path, "django.contrib.postgres.indexes.BloomIndex")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs,
            {
                "fields": ["title"],
                "name": "test_bloom",
                "length": 80,
                "columns": [4],
            },
        )