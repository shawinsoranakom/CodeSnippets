def test_deconstruction(self):
        index = GinIndex(
            fields=["title"],
            name="test_title_gin",
            fastupdate=True,
            gin_pending_list_limit=128,
        )
        path, args, kwargs = index.deconstruct()
        self.assertEqual(path, "django.contrib.postgres.indexes.GinIndex")
        self.assertEqual(args, ())
        self.assertEqual(
            kwargs,
            {
                "fields": ["title"],
                "name": "test_title_gin",
                "fastupdate": True,
                "gin_pending_list_limit": 128,
            },
        )